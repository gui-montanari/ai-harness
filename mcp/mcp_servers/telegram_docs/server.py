#!/usr/bin/env python3
"""MCP read-only para consultar exclusivamente a documentação oficial do Telegram."""

from __future__ import annotations

import hashlib
import json
import os
import re
import sys
import time
import unicodedata
from dataclasses import dataclass
from html.parser import HTMLParser
from pathlib import Path
from typing import Any
from urllib import error as urllib_error
from urllib import parse as urllib_parse
from urllib import request as urllib_request


SERVER_NAME = "telegram-docs"
SERVER_VERSION = "1.0.0"
OFFICIAL_HOST = "core.telegram.org"
DEFAULT_CACHE_TTL_SECONDS = 21_600
MAX_DOCUMENT_BYTES = 8_000_000
DEFAULT_MAX_CHARS = 12_000
MAX_RESULT_CHARS = 30_000
USER_AGENT = "AutodinTelegramDocsMCP/1.0 (+https://core.telegram.org)"

DOCUMENTS: dict[str, dict[str, str]] = {
    "bots": {
        "url": "https://core.telegram.org/bots",
        "description": "Introdução, criação, capacidades e limitações de bots.",
    },
    "bot-api": {
        "url": "https://core.telegram.org/bots/api",
        "description": "Referência completa de métodos e tipos da Telegram Bot API.",
    },
    "bot-api-changelog": {
        "url": "https://core.telegram.org/bots/api-changelog",
        "description": "Histórico oficial de mudanças da Telegram Bot API.",
    },
    "bot-features": {
        "url": "https://core.telegram.org/bots/features",
        "description": "Deep links, comandos, privacidade, grupos e recursos de bots.",
    },
    "telegram-login": {
        "url": "https://core.telegram.org/bots/webapps",
        "description": "Telegram Login/OIDC, Mini Apps e autorização para mensagens.",
    },
    "deep-links": {
        "url": "https://core.telegram.org/api/links",
        "description": "Links t.me e tg://, parâmetros start e abertura de bots.",
    },
    "webhooks": {
        "url": "https://core.telegram.org/bots/webhooks",
        "description": "Guia oficial de webhooks para bots.",
    },
    "tdlib": {
        "url": "https://core.telegram.org/tdlib",
        "description": "Biblioteca oficial para clientes Telegram completos.",
    },
    "api-id": {
        "url": "https://core.telegram.org/api/obtaining_api_id",
        "description": "Criação de aplicações e obtenção de api_id/api_hash.",
    },
}


@dataclass(frozen=True, slots=True)
class Section:
    level: int
    title: str
    anchor: str
    text: str


@dataclass(frozen=True, slots=True)
class ParsedDocument:
    url: str
    title: str
    sections: tuple[Section, ...]
    fetched_at: float
    cache_state: str


class TelegramDocsHTMLParser(HTMLParser):
    """Extrai blocos por heading sem depender da estrutura visual do site."""

    _ignored_tags = {"script", "style", "svg", "noscript"}
    _block_tags = {
        "address",
        "blockquote",
        "br",
        "div",
        "dl",
        "dt",
        "dd",
        "li",
        "p",
        "pre",
        "table",
        "tr",
        "ul",
        "ol",
    }

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._ignored_depth = 0
        self._heading_level: int | None = None
        self._heading_anchor = ""
        self._heading_parts: list[str] = []
        self._content_parts: list[str] = []
        self._sections: list[Section] = []
        self._document_title = ""

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in self._ignored_tags:
            self._ignored_depth += 1
            return
        if self._ignored_depth:
            return
        attributes = dict(attrs)
        if re.fullmatch(r"h[1-6]", tag):
            self._flush_section()
            self._heading_level = int(tag[1])
            self._heading_anchor = attributes.get("id") or ""
            self._heading_parts = []
            return
        if self._heading_level is not None and tag == "a":
            self._heading_anchor = (
                self._heading_anchor
                or attributes.get("name")
                or attributes.get("id")
                or ""
            )
        if tag in {"td", "th"}:
            self._content_parts.append(" | ")
        elif tag == "li":
            self._content_parts.append("\n- ")
        elif tag in self._block_tags:
            self._content_parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if tag in self._ignored_tags:
            self._ignored_depth = max(0, self._ignored_depth - 1)
            return
        if self._ignored_depth:
            return
        if re.fullmatch(r"h[1-6]", tag) and self._heading_level is not None:
            title = _clean_text(" ".join(self._heading_parts))
            if title and not self._document_title:
                self._document_title = title
            self._heading_parts = [title]
            return
        if tag in self._block_tags:
            self._content_parts.append("\n")

    def handle_data(self, data: str) -> None:
        if self._ignored_depth or not data.strip():
            return
        if self._heading_level is not None and self._heading_parts == []:
            self._heading_parts.append(data)
        else:
            self._content_parts.append(data)

    def close(self) -> None:
        super().close()
        self._flush_section()

    def parsed(self, *, url: str, fetched_at: float, cache_state: str) -> ParsedDocument:
        title = self._document_title or url
        return ParsedDocument(
            url=url,
            title=title,
            sections=tuple(self._sections),
            fetched_at=fetched_at,
            cache_state=cache_state,
        )

    def _flush_section(self) -> None:
        if self._heading_level is None:
            self._content_parts = []
            return
        title = _clean_text(" ".join(self._heading_parts))
        text = _clean_text("".join(self._content_parts))
        if title or text:
            self._sections.append(
                Section(
                    level=self._heading_level,
                    title=title or "(sem título)",
                    anchor=self._heading_anchor,
                    text=text,
                )
            )
        self._heading_level = None
        self._heading_anchor = ""
        self._heading_parts = []
        self._content_parts = []


def _clean_text(value: str) -> str:
    value = value.replace("\r", "")
    lines = []
    for raw_line in value.splitlines():
        line = re.sub(r"[ \t]+", " ", raw_line).strip()
        if line and (not lines or line != lines[-1]):
            lines.append(line)
    return "\n".join(lines).strip()


def _normalize(value: str) -> str:
    ascii_value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", " ", ascii_value.casefold()).strip()


def _cache_dir() -> Path:
    configured = os.getenv("TELEGRAM_DOCS_CACHE_DIR")
    if configured:
        return Path(configured).expanduser()
    xdg_cache = os.getenv("XDG_CACHE_HOME")
    base = Path(xdg_cache).expanduser() if xdg_cache else Path.home() / ".cache"
    return base / "ai-harness" / "telegram-docs"


def _cache_ttl_seconds() -> int:
    raw = os.getenv("TELEGRAM_DOCS_CACHE_TTL_SECONDS", str(DEFAULT_CACHE_TTL_SECONDS))
    try:
        return max(300, min(int(raw), 604_800))
    except ValueError:
        return DEFAULT_CACHE_TTL_SECONDS


def _validate_official_url(path_or_url: str) -> str:
    if not isinstance(path_or_url, str) or not path_or_url.strip():
        raise ValueError("Informe uma página ou URL da documentação do Telegram.")
    value = path_or_url.strip()
    if value in DOCUMENTS:
        value = DOCUMENTS[value]["url"]
    elif value.startswith("/"):
        value = f"https://{OFFICIAL_HOST}{value}"
    elif not urllib_parse.urlsplit(value).scheme:
        value = f"https://{OFFICIAL_HOST}/{value.lstrip('/')}"
    parsed = urllib_parse.urlsplit(value)
    if parsed.scheme != "https" or parsed.hostname != OFFICIAL_HOST:
        raise ValueError(
            "Somente URLs HTTPS de https://core.telegram.org são permitidas."
        )
    if parsed.username or parsed.password or parsed.port not in (None, 443):
        raise ValueError("A URL oficial não pode conter credenciais nem porta não padrão.")
    return urllib_parse.urlunsplit(("https", OFFICIAL_HOST, parsed.path or "/", parsed.query, ""))


def _cache_paths(url: str) -> tuple[Path, Path]:
    digest = hashlib.sha256(url.encode("utf-8")).hexdigest()
    cache_dir = _cache_dir()
    return cache_dir / f"{digest}.html", cache_dir / f"{digest}.json"


class OfficialTelegramRedirectHandler(urllib_request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        _validate_official_url(newurl)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def _read_cache(url: str) -> tuple[str, float] | None:
    html_path, metadata_path = _cache_paths(url)
    try:
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        if metadata.get("url") != url:
            return None
        return html_path.read_text(encoding="utf-8"), float(metadata["fetched_at"])
    except (OSError, ValueError, KeyError, json.JSONDecodeError):
        return None


def _write_cache(url: str, html: str, fetched_at: float) -> None:
    html_path, metadata_path = _cache_paths(url)
    html_path.parent.mkdir(parents=True, exist_ok=True)
    html_tmp = html_path.with_suffix(".html.tmp")
    metadata_tmp = metadata_path.with_suffix(".json.tmp")
    html_tmp.write_text(html, encoding="utf-8")
    metadata_tmp.write_text(
        json.dumps({"url": url, "fetched_at": fetched_at}, ensure_ascii=False),
        encoding="utf-8",
    )
    html_tmp.replace(html_path)
    metadata_tmp.replace(metadata_path)


def _download(url: str) -> tuple[str, str]:
    request = urllib_request.Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "text/html,application/xhtml+xml",
        },
    )
    opener = urllib_request.build_opener(OfficialTelegramRedirectHandler())
    with opener.open(request, timeout=20) as response:
        final_url = _validate_official_url(response.geturl())
        content_type = response.headers.get_content_type()
        if content_type not in {"text/html", "application/xhtml+xml"}:
            raise ValueError(f"Conteúdo oficial não suportado: {content_type}.")
        raw = response.read(MAX_DOCUMENT_BYTES + 1)
        if len(raw) > MAX_DOCUMENT_BYTES:
            raise ValueError(f"Documento excede {MAX_DOCUMENT_BYTES} bytes.")
        charset = response.headers.get_content_charset() or "utf-8"
        return raw.decode(charset, errors="replace"), final_url


def _load_document(path_or_url: str, *, refresh: bool = False) -> ParsedDocument:
    url = _validate_official_url(path_or_url)
    cached = _read_cache(url)
    now = time.time()
    cache_fresh = cached is not None and now - cached[1] <= _cache_ttl_seconds()
    if cache_fresh and not refresh:
        html, fetched_at = cached
        cache_state = "fresh-cache"
    else:
        try:
            html, final_url = _download(url)
            url = final_url
            fetched_at = now
            cache_state = "network"
            _write_cache(url, html, fetched_at)
        except (OSError, ValueError, urllib_error.URLError) as error:
            if cached is None:
                raise RuntimeError(f"Não foi possível obter a documentação oficial: {error}") from error
            html, fetched_at = cached
            cache_state = "stale-cache"
    parser = TelegramDocsHTMLParser()
    parser.feed(html)
    parser.close()
    document = parser.parsed(url=url, fetched_at=fetched_at, cache_state=cache_state)
    if not document.sections:
        raise RuntimeError("A página oficial não contém seções textuais reconhecíveis.")
    return document


def _source_url(document: ParsedDocument, section: Section | None = None) -> str:
    if section and section.anchor:
        return f"{document.url}#{section.anchor}"
    return document.url


def _section_markdown(section: Section) -> str:
    body = section.text.strip()
    return f"{'#' * min(section.level, 6)} {section.title}\n\n{body}".strip()


def _document_metadata(document: ParsedDocument) -> str:
    fetched_at = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(document.fetched_at))
    return f"Fonte oficial: {document.url}\nObtida em: {fetched_at}\nOrigem: {document.cache_state}"


def list_sources() -> str:
    lines = [
        "# Fontes oficiais disponíveis",
        "",
        "Este MCP não possui credenciais do Telegram e não executa ações operacionais.",
        "",
    ]
    for key, item in DOCUMENTS.items():
        lines.extend((f"- `{key}` — {item['description']}", f"  {item['url']}"))
    return "\n".join(lines)


def fetch_document(
    path_or_url: str,
    *,
    section: str = "",
    max_chars: int = DEFAULT_MAX_CHARS,
    refresh: bool = False,
) -> str:
    document = _load_document(path_or_url, refresh=refresh)
    max_chars = max(1_000, min(int(max_chars), MAX_RESULT_CHARS))
    chosen: list[Section]
    if section.strip():
        normalized = _normalize(section)
        exact = [
            item
            for item in document.sections
            if normalized in {_normalize(item.title), _normalize(item.anchor)}
        ]
        partial = [
            item
            for item in document.sections
            if normalized in _normalize(f"{item.title} {item.anchor}")
        ]
        chosen = exact or partial
        if not chosen:
            raise ValueError(f"Seção não encontrada na página oficial: {section}")
    else:
        chosen = list(document.sections)
    body = "\n\n".join(_section_markdown(item) for item in chosen)
    if len(body) > max_chars:
        body = body[:max_chars].rstrip() + "\n\n[conteúdo truncado pelo limite solicitado]"
    source = _source_url(document, chosen[0] if len(chosen) == 1 else None)
    metadata = _document_metadata(document).replace(document.url, source, 1)
    return f"{body}\n\n---\n{metadata}"


def _snippet(text: str, terms: list[str], limit: int = 600) -> str:
    cleaned = _clean_text(text)
    normalized = _normalize(cleaned)
    positions = [normalized.find(term) for term in terms if normalized.find(term) >= 0]
    start = max(0, (min(positions) if positions else 0) - 120)
    snippet = cleaned[start : start + limit].strip()
    if start:
        snippet = "…" + snippet
    if start + limit < len(cleaned):
        snippet += "…"
    return snippet


def search_documents(
    query: str,
    *,
    sources: list[str] | None = None,
    max_results: int = 8,
    refresh: bool = False,
) -> str:
    if not isinstance(query, str) or not query.strip():
        raise ValueError("A consulta não pode ficar vazia.")
    terms = [term for term in _normalize(query).split() if len(term) > 1]
    if not terms:
        raise ValueError("A consulta precisa conter termos pesquisáveis.")
    selected = sources or list(DOCUMENTS)
    unknown = sorted(set(selected) - set(DOCUMENTS))
    if unknown:
        raise ValueError(f"Fontes desconhecidas: {', '.join(unknown)}")
    max_results = max(1, min(int(max_results), 20))
    matches: list[tuple[int, ParsedDocument, Section]] = []
    errors: list[str] = []
    for source in selected:
        try:
            document = _load_document(source, refresh=refresh)
        except Exception as error:
            errors.append(f"{source}: {error}")
            continue
        for section in document.sections:
            title = _normalize(section.title)
            anchor = _normalize(section.anchor)
            body = _normalize(section.text)
            if not all(term in f"{title} {anchor} {body}" for term in terms):
                continue
            score = 0
            phrase = _normalize(query)
            score += 80 if phrase and phrase in title else 0
            score += 60 if phrase and phrase in anchor else 0
            score += sum(20 for term in terms if term in title)
            score += sum(12 for term in terms if term in anchor)
            score += min(30, sum(body.count(term) for term in terms))
            matches.append((score, document, section))
    matches.sort(key=lambda item: (-item[0], item[1].url, item[2].title))
    if not matches:
        detail = f"\nFalhas parciais: {'; '.join(errors)}" if errors else ""
        return f"Nenhum resultado oficial encontrado para `{query}`.{detail}"
    lines = [f"# Resultados oficiais para: {query}", ""]
    for index, (_, document, section) in enumerate(matches[:max_results], start=1):
        lines.extend(
            (
                f"## {index}. {section.title}",
                _snippet(section.text, terms),
                f"Fonte: {_source_url(document, section)}",
                f"Origem: {document.cache_state}",
                "",
            )
        )
    if errors:
        lines.extend(("## Avisos", *[f"- {error}" for error in errors]))
    return "\n".join(lines).strip()


def bot_api_reference(name: str, *, refresh: bool = False) -> str:
    if not isinstance(name, str) or not name.strip():
        raise ValueError("Informe o nome de um método ou tipo da Bot API.")
    document = _load_document("bot-api", refresh=refresh)
    normalized = _normalize(name)
    exact = [
        section
        for section in document.sections
        if normalized in {_normalize(section.title), _normalize(section.anchor)}
    ]
    if not exact:
        suggestions = [
            section.title
            for section in document.sections
            if normalized in _normalize(f"{section.title} {section.anchor}")
        ][:8]
        suffix = f" Sugestões: {', '.join(suggestions)}." if suggestions else ""
        raise ValueError(f"Referência `{name}` não encontrada na Bot API.{suffix}")
    section = exact[0]
    body = _section_markdown(section)
    if len(body) > MAX_RESULT_CHARS:
        body = body[:MAX_RESULT_CHARS].rstrip() + "\n\n[conteúdo truncado]"
    return (
        f"{body}\n\n---\n"
        f"Fonte oficial: {_source_url(document, section)}\n"
        f"Origem: {document.cache_state}"
    )


READ_ONLY_ANNOTATIONS = {
    "readOnlyHint": True,
    "destructiveHint": False,
    "idempotentHint": True,
    "openWorldHint": True,
}

TOOLS = [
    {
        "name": "list_telegram_doc_sources",
        "description": (
            "Lista as fontes oficiais do Telegram disponíveis neste MCP read-only. "
            "Use antes de uma busca quando precisar restringir o tema."
        ),
        "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False},
        "annotations": READ_ONLY_ANNOTATIONS,
    },
    {
        "name": "search_telegram_docs",
        "description": (
            "Pesquisa conceitos nas páginas oficiais de core.telegram.org e retorna trechos "
            "com links para a fonte. Não consulta blogs ou implementações comunitárias."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "minLength": 2, "maxLength": 300},
                "sources": {
                    "type": "array",
                    "items": {"type": "string", "enum": list(DOCUMENTS)},
                    "uniqueItems": True,
                },
                "max_results": {"type": "integer", "minimum": 1, "maximum": 20, "default": 8},
                "refresh": {
                    "type": "boolean",
                    "default": False,
                    "description": "Ignora cache fresco e tenta baixar novamente.",
                },
            },
            "required": ["query"],
            "additionalProperties": False,
        },
        "annotations": READ_ONLY_ANNOTATIONS,
    },
    {
        "name": "fetch_telegram_doc",
        "description": (
            "Lê uma página ou seção oficial do Telegram. Aceita uma chave listada pelo MCP, "
            "um caminho de core.telegram.org ou uma URL HTTPS desse domínio."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "path_or_url": {"type": "string", "minLength": 1, "maxLength": 2_000},
                "section": {"type": "string", "maxLength": 300, "default": ""},
                "max_chars": {
                    "type": "integer",
                    "minimum": 1_000,
                    "maximum": MAX_RESULT_CHARS,
                    "default": DEFAULT_MAX_CHARS,
                },
                "refresh": {"type": "boolean", "default": False},
            },
            "required": ["path_or_url"],
            "additionalProperties": False,
        },
        "annotations": READ_ONLY_ANNOTATIONS,
    },
    {
        "name": "get_telegram_bot_api_reference",
        "description": (
            "Obtém a seção oficial exata de um método ou tipo da Telegram Bot API, "
            "por exemplo sendMessage, setWebhook, Update ou InlineKeyboardMarkup."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "minLength": 1, "maxLength": 200},
                "refresh": {"type": "boolean", "default": False},
            },
            "required": ["name"],
            "additionalProperties": False,
        },
        "annotations": READ_ONLY_ANNOTATIONS,
    },
]


def _result(request_id: object, result: object | None = None, error: object | None = None) -> dict:
    response: dict[str, object] = {"jsonrpc": "2.0", "id": request_id}
    if error is not None:
        response["error"] = error
    else:
        response["result"] = result
    return response


def _tool_text(text: str, *, is_error: bool = False) -> dict[str, object]:
    return {
        "content": [{"type": "text", "text": text}],
        "isError": is_error,
    }


def _handle(message: dict[str, Any]) -> dict | None:
    method = message.get("method")
    request_id = message.get("id")
    if method == "initialize":
        requested = message.get("params", {}).get("protocolVersion", "2024-11-05")
        return _result(
            request_id,
            {
                "protocolVersion": requested,
                "capabilities": {"tools": {"listChanged": False}},
                "serverInfo": {"name": SERVER_NAME, "version": SERVER_VERSION},
                "instructions": (
                    "Servidor read-only para documentação oficial do Telegram. "
                    "Use as ferramentas para confirmar APIs, parâmetros e limitações atuais. "
                    "Trate os links core.telegram.org retornados como fonte e não confunda "
                    "este servidor com uma integração operacional ou com acesso a contas."
                ),
            },
        )
    if method == "tools/list":
        return _result(request_id, {"tools": TOOLS})
    if method == "tools/call":
        params = message.get("params") or {}
        name = params.get("name")
        arguments = params.get("arguments") or {}
        try:
            if name == "list_telegram_doc_sources":
                text = list_sources()
            elif name == "search_telegram_docs":
                text = search_documents(
                    arguments.get("query"),
                    sources=arguments.get("sources"),
                    max_results=arguments.get("max_results", 8),
                    refresh=arguments.get("refresh", False),
                )
            elif name == "fetch_telegram_doc":
                text = fetch_document(
                    arguments.get("path_or_url"),
                    section=arguments.get("section", ""),
                    max_chars=arguments.get("max_chars", DEFAULT_MAX_CHARS),
                    refresh=arguments.get("refresh", False),
                )
            elif name == "get_telegram_bot_api_reference":
                text = bot_api_reference(
                    arguments.get("name"),
                    refresh=arguments.get("refresh", False),
                )
            else:
                return _result(
                    request_id,
                    error={"code": -32601, "message": f"Ferramenta desconhecida: {name}"},
                )
            return _result(request_id, _tool_text(text))
        except Exception as error:
            return _result(request_id, _tool_text(str(error), is_error=True))
    if method == "ping":
        return _result(request_id, {})
    if request_id is None:
        return None
    return _result(
        request_id,
        error={"code": -32601, "message": f"Método desconhecido: {method}"},
    )


def main() -> None:
    for line in sys.stdin:
        try:
            message = json.loads(line)
            response = _handle(message)
            if response is not None:
                print(json.dumps(response, ensure_ascii=False), flush=True)
        except Exception as error:
            print(
                json.dumps(
                    _result(None, error={"code": -32603, "message": str(error)}),
                    ensure_ascii=False,
                ),
                flush=True,
            )


if __name__ == "__main__":
    main()

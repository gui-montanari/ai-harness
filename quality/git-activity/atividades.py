"""Markdown de worktrees/ATIVIDADES.md."""

from __future__ import annotations

import re

from ledger import ActivityRow, HEADERS, PREAMBLE

SECTION_RE = re.compile(r"^## (.+)$", re.M)


def _preamble_and_sections(text: str) -> tuple[str, list[tuple[str, str]]]:
    matches = list(SECTION_RE.finditer(text))
    if not matches:
        return text.strip(), []
    preamble = text[: matches[0].start()].strip()
    ordered: list[tuple[str, str]] = []
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        ordered.append((match.group(1).strip(), text[match.start() : end].strip()))
    return preamble, ordered


def render_table(rows: list[ActivityRow]) -> str:
    lines = [
        "| " + " | ".join(HEADERS) + " |",
        "| " + " | ".join("---" for _ in HEADERS) + " |",
    ]
    for row in rows:
        cells = [
            row.pasta,
            row.kind,
            row.slug,
            row.branch,
            row.sha,
            row.pr_prod,
            row.merge_prod,
            row.pr_develop,
            row.merge_develop,
            row.estado,
        ]
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines)


def render_ledger(repo: str, rows: list[ActivityRow], *, updated: str) -> str:
    body = render_table(rows)
    return f"{PREAMBLE}\nAtualizado: {updated}\n\n## {repo}\n\n{body}\n"


def parse_ledger(text: str) -> dict[str, list[ActivityRow]]:
    _, sections = _preamble_and_sections(text)
    return {repo: _parse_table(repo, body) for repo, body in sections}


def _parse_table(repo: str, body: str) -> list[ActivityRow]:
    lines = [line.strip() for line in body.splitlines() if line.strip().startswith("|")]
    if len(lines) < 3:
        return []
    headers = [cell.strip() for cell in lines[0].strip("|").split("|")]
    rows: list[ActivityRow] = []
    for line in lines[2:]:
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if len(cells) < len(HEADERS):
            continue
        rec = dict(zip(headers, cells, strict=False))
        rows.append(
            ActivityRow(
                repo=repo,
                pasta=rec.get("pasta", "—"),
                kind=rec.get("kind", ""),
                slug=rec.get("slug", ""),
                branch=rec.get("branch", ""),
                sha=rec.get("sha", ""),
                pr_prod=rec.get("PR produção", "—"),
                merge_prod=rec.get("merge produção", "—"),
                pr_develop=rec.get("PR develop", "—"),
                merge_develop=rec.get("merge develop", "—"),
                estado=rec.get("estado", "aberta"),
            )
        )
    return rows


def upsert_section(existing: str, repo: str, incoming: str) -> str:
    in_preamble, in_sections = _preamble_and_sections(incoming)
    incoming_map = dict(in_sections)
    new_body = incoming_map.get(repo)
    if new_body is None:
        new_body = in_sections[0][1] if in_sections else incoming.strip()
    ex_preamble, ex_sections = (
        _preamble_and_sections(existing) if existing.strip() else (in_preamble, [])
    )
    order: list[tuple[str, str]] = []
    seen: set[str] = set()
    for name, body in ex_sections:
        order.append((repo, new_body) if name == repo else (name, body))
        seen.add(name)
    if repo not in seen:
        order.append((repo, new_body))
    parts = [in_preamble or ex_preamble or PREAMBLE.strip(), ""]
    for _, body in order:
        parts.extend([body, ""])
    return "\n".join(parts).strip() + "\n"

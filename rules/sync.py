#!/usr/bin/env python3
"""Projeta rules do harness em cada host: nativo por symlink; Codex/Agents por AGENTS.md."""

from __future__ import annotations

import re
from pathlib import Path

HOME = Path.home()
CANON = HOME / ".local/share/ai-harness"
PUBLIC = Path(__file__).resolve().parent
OVERLAY = HOME / ".config/ai-harness/overlay/rules"

MARKER_START = "<!-- ai-harness-rules -->"
MARKER_END = "<!-- /ai-harness-rules -->"
LEGACY_START = "<!-- gui-montanari-skills -->"
LEGACY_END = "<!-- /gui-montanari-skills -->"

SYMLINK_HOSTS = (
    (".grok/rules", ".md"),
    (".cursor/rules", ".mdc"),
    (".claude/rules", ".md"),
    (".agents/rules", ".md"),
    (".codex/rules", ".md"),
    (".gemini/config/rules", ".md"),
)

INJECT_RELATIVE = (".codex/AGENTS.md", ".agents/AGENTS.md")
STRIP_RELATIVE = (".claude/CLAUDE.md",)
NATIVE_KEYS = ("rules", "hooks", "agents", "skills", "mcps")


class Rule:
    def __init__(self, name: str, path: Path, overlay: bool) -> None:
        self.name = name
        self.path = path
        self.overlay = overlay


def _md_files(folder: Path) -> list[Path]:
    if not folder.is_dir():
        return []
    return sorted(
        p
        for p in folder.iterdir()
        if p.is_file()
        and p.suffix == ".md"
        and p.name != "README.md"
        and not p.name.endswith(".example.md")
    )


def catalog() -> list[Rule]:
    by_name: dict[str, Rule] = {}
    for path in _md_files(PUBLIC):
        by_name[path.stem] = Rule(path.stem, path, False)
    for path in _md_files(OVERLAY):
        by_name[path.stem] = Rule(path.stem, path, True)
    return list(by_name.values())


def _strip_marked(text: str, start: str, end: str) -> str:
    if start not in text:
        return text
    out: list[str] = []
    skip = False
    for line in text.splitlines(keepends=True):
        stripped = line.rstrip("\n")
        if stripped == start:
            skip = True
            continue
        if skip and stripped == end:
            skip = False
            continue
        if not skip:
            out.append(line)
    return "".join(out)


def _upsert_marked(text: str, body: str) -> str:
    text = _strip_marked(text, LEGACY_START, LEGACY_END)
    text = _strip_marked(text, MARKER_START, MARKER_END)
    block = f"{MARKER_START}\n{body.rstrip()}\n{MARKER_END}\n"
    if text.strip():
        return text.rstrip() + "\n\n" + block
    return block


def _inject_body(items: list[Rule]) -> str:
    parts = [item.path.read_text() for item in sorted(items, key=lambda r: r.name)]
    return "\n\n".join(p.strip() + "\n" for p in parts)


def migrate_stray_copies() -> None:
    public_names = {p.stem for p in _md_files(PUBLIC)}
    OVERLAY.mkdir(parents=True, exist_ok=True)
    for rel, ext in SYMLINK_HOSTS:
        folder = HOME / rel
        if not folder.is_dir():
            continue
        for path in list(folder.iterdir()):
            if not path.is_file() or path.is_symlink():
                continue
            if path.suffix not in {".md", ".mdc"}:
                continue
            if path.stem in public_names:
                continue
            dest = OVERLAY / f"{path.stem}.md"
            if not dest.exists():
                dest.write_text(path.read_text())
            path.unlink()


def _symlink_hosts(items: list[Rule]) -> None:
    for rel, ext in SYMLINK_HOSTS:
        dest_dir = HOME / rel
        dest_dir.mkdir(parents=True, exist_ok=True)
        for item in items:
            dest = dest_dir / f"{item.name}{ext}"
            if dest.exists() or dest.is_symlink():
                dest.unlink()
            dest.symlink_to(item.path)
        stale = dest_dir / "constituicao-e-skills.md"
        if stale.exists() or stale.is_symlink():
            stale.unlink()


def _write_inject(items: list[Rule]) -> None:
    body = _inject_body(items)
    for rel in INJECT_RELATIVE:
        path = HOME / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        current = path.read_text() if path.exists() else ""
        path.write_text(_upsert_marked(current, body))
    for rel in STRIP_RELATIVE:
        path = HOME / rel
        if not path.exists():
            continue
        path.write_text(
            _strip_marked(
                _strip_marked(path.read_text(), LEGACY_START, LEGACY_END),
                MARKER_START,
                MARKER_END,
            )
        )


def _replace_compat_section(text: str, section: str) -> str:
    header = f"[compat.{section}]"
    pattern = rf"\[compat\.{re.escape(section)}\](.*?)(?=\n\[|\Z)"
    owned = "".join(f"{key} = false\n" for key in NATIVE_KEYS)
    match = re.search(pattern, text, re.S)
    extra: list[str] = []
    if match:
        for line in match.group(1).splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            key = stripped.split("=", 1)[0].strip()
            if key in NATIVE_KEYS:
                continue
            extra.append(line.rstrip())
        inner = "\n" + owned
        if extra:
            inner += "\n".join(extra) + "\n"
        return text[: match.start()] + header + inner + text[match.end() :]
    return text.rstrip() + f"\n\n{header}\n{owned}"


def ensure_grok_compat(text: str) -> str:
    comment = (
        "# ai-harness: Grok só lê nativo (~/.grok/{rules,hooks,skills} + mcp no config.toml).\n"
    )
    drop = (
        "gui-montanari-skills: catalog rules",
        "Keep vendor rule scan off",
        "rules/hooks nativos em ~/.grok",
        "Grok só lê nativo",
    )
    lines = [
        line
        for line in text.splitlines(keepends=True)
        if not (line.lstrip().startswith("#") and any(token in line for token in drop))
    ]
    out = "".join(lines)
    for section in ("cursor", "claude"):
        out = _replace_compat_section(out, section)
    if "ai-harness: Grok só lê nativo" not in out:
        out = out.replace("[compat.cursor]", comment + "[compat.cursor]", 1)
    if not out.endswith("\n"):
        out += "\n"
    return out


def sync_grok_compat() -> None:
    cfg = HOME / ".grok" / "config.toml"
    cfg.parent.mkdir(parents=True, exist_ok=True)
    current = cfg.read_text() if cfg.exists() else ""
    cfg.write_text(ensure_grok_compat(current))


def sync() -> None:
    migrate_stray_copies()
    items = catalog()
    _symlink_hosts(items)
    _write_inject(items)
    sync_grok_compat()


def main() -> None:
    sync()
    public = sum(1 for item in catalog() if not item.overlay)
    overlay = sum(1 for item in catalog() if item.overlay)
    print(f"rules: {public} globais + {overlay} overlay")


if __name__ == "__main__":
    main()

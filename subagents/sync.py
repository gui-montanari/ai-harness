#!/usr/bin/env python3
"""Projeta subagents do harness em cada host: nativo por symlink. Overlay fora do git público."""

from __future__ import annotations

from pathlib import Path

HOME = Path.home()
PUBLIC = Path(__file__).resolve().parent
OVERLAY = HOME / ".config/ai-harness/overlay/subagents"
LEGACY_OVERLAY = HOME / ".config/ai-harness/overlay/agents"

SYMLINK_HOSTS = (
    ".cursor/agents",
    ".claude/agents",
)

PUBLIC_FASTAPI = (
    "python-fastapi-architect",
    "python-fastapi-master",
    "python-fastapi-test-specialist",
    "fastapi-async-debugger",
    "frontend-specialist-fastapi",
)


class Agent:
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


def migrate_legacy_overlay() -> None:
    public_names = {p.stem for p in _md_files(PUBLIC)}
    if not LEGACY_OVERLAY.is_dir():
        return
    OVERLAY.mkdir(parents=True, exist_ok=True)
    for path in list(_md_files(LEGACY_OVERLAY)):
        if path.stem in public_names:
            path.unlink()
            continue
        dest = OVERLAY / path.name
        if not dest.exists():
            dest.write_text(path.read_text())
        path.unlink()
    leftover = [p for p in LEGACY_OVERLAY.iterdir() if p.name != "__pycache__"]
    if not leftover:
        LEGACY_OVERLAY.rmdir()


def catalog() -> list[Agent]:
    migrate_legacy_overlay()
    by_name: dict[str, Agent] = {}
    for path in _md_files(PUBLIC):
        by_name[path.stem] = Agent(path.stem, path, False)
    for path in _md_files(OVERLAY):
        by_name[path.stem] = Agent(path.stem, path, True)
    return list(by_name.values())


def migrate_stray_copies() -> None:
    public_names = {p.stem for p in _md_files(PUBLIC)}
    OVERLAY.mkdir(parents=True, exist_ok=True)
    for rel in SYMLINK_HOSTS:
        folder = HOME / rel
        if not folder.is_dir():
            continue
        for path in list(folder.iterdir()):
            if not path.is_file() or path.is_symlink():
                continue
            if path.suffix != ".md":
                continue
            if path.stem in public_names:
                continue
            dest = OVERLAY / f"{path.stem}.md"
            if not dest.exists():
                dest.write_text(path.read_text())
            path.unlink()


def _symlink_hosts(items: list[Agent]) -> None:
    wanted = {item.name for item in items}
    overlay_roots = {OVERLAY.resolve()}
    if LEGACY_OVERLAY.exists():
        overlay_roots.add(LEGACY_OVERLAY.resolve())
    for rel in SYMLINK_HOSTS:
        dest_dir = HOME / rel
        dest_dir.mkdir(parents=True, exist_ok=True)
        for item in items:
            dest = dest_dir / f"{item.name}.md"
            if dest.exists() or dest.is_symlink():
                dest.unlink()
            dest.symlink_to(item.path)
        for path in list(dest_dir.iterdir()):
            if not path.is_symlink():
                continue
            if path.stem in wanted:
                continue
            target = path.resolve()
            if target.parent in {PUBLIC.resolve(), *overlay_roots}:
                path.unlink()


def sync() -> None:
    migrate_legacy_overlay()
    migrate_stray_copies()
    _symlink_hosts(catalog())


def main() -> None:
    sync()
    public = sum(1 for item in catalog() if not item.overlay)
    overlay = sum(1 for item in catalog() if item.overlay)
    print(f"subagents: {public} globais + {overlay} overlay")


if __name__ == "__main__":
    main()

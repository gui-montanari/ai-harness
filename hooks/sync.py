#!/usr/bin/env python3
"""Injeta o catálogo de hooks em todos os hosts. Overlay de máquina entra depois."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
HOME = Path.home()
CANON = HOME / ".local/share/ai-harness"
OVERLAY = HOME / ".config/ai-harness/overlay/hooks"
CATALOG_PATH = ROOT / "catalog.json"
MARKER = "ai-harness/hooks"


def load_json(path: Path, default):
    if not path.exists():
        return default
    text = path.read_text()
    return json.loads(text) if text.strip() else default


def catalog() -> dict[str, dict]:
    data = load_json(CATALOG_PATH, {"hooks": {}})
    items = dict(data.get("hooks") or {})
    overlay_cat = OVERLAY / "catalog.json"
    if overlay_cat.exists():
        extra = load_json(overlay_cat, {"hooks": {}}).get("hooks") or {}
        for name, spec in extra.items():
            spec = dict(spec)
            spec["_overlay"] = True
            items[name] = spec
    return items


def script_path(spec: dict) -> Path:
    name = spec["script"]
    if spec.get("_overlay"):
        return OVERLAY / "scripts" / name
    return CANON / "hooks" / "scripts" / name


def command_line(spec: dict, *, grok: bool = False) -> str:
    path = script_path(spec)
    runtime = spec.get("runtime") or ("python3" if path.suffix == ".py" else "bash")
    # Grok: caminho absoluto sem aspas. Se começar com aspas, prefixa ~/.grok/hooks/.
    # Se começar com "python3 ", trata como shell; o execve do Grok no .py com
    # shebang é o caminho estável (os .sh antigos sumiram e a sessão 2/7 quebrava).
    if grok:
        return str(path)
    if runtime == "python3":
        return f"python3 {path}"
    if runtime == "bash":
        return str(path)
    return f"{runtime} {path}"


def grok_json(name: str, spec: dict) -> dict:
    hooks: dict = {}
    for event, cfg in (spec.get("events") or {}).items():
        group: dict = {"hooks": [{"type": "command", "command": command_line(spec, grok=True), "timeout": spec.get("timeout", 5)}]}
        matcher = (cfg or {}).get("matcher")
        if matcher:
            group["matcher"] = matcher
        hooks.setdefault(event, []).append(group)
    return {"hooks": hooks}


def sync_grok(items: dict[str, dict]) -> None:
    dest = HOME / ".grok" / "hooks"
    dest.mkdir(parents=True, exist_ok=True)
    managed = set(items)
    for name, spec in items.items():
        path = dest / f"{name}.json"
        if path.exists() or path.is_symlink():
            path.unlink()
        script = script_path(spec)
        if script.is_file():
            script.chmod(script.stat().st_mode | 0o111)
        path.write_text(json.dumps(grok_json(name, spec), indent=2) + "\n")
    for path in dest.glob("*.json"):
        if path.stem not in managed and _managed_command(path.read_text(errors="replace")):
            path.unlink()


def _managed_command(text: str) -> bool:
    return MARKER in text or "ai-harness/overlay/hooks" in text or str(OVERLAY) in text


def _strip_handlers(handlers: list, script_names: set[str]) -> list:
    kept = []
    for item in handlers:
        blob = json.dumps(item)
        if _managed_command(blob):
            continue
        if any(script in blob for script in script_names):
            continue
        kept.append(item)
    return kept


def sync_cursor(items: dict[str, dict]) -> None:
    dest = HOME / ".cursor" / "hooks.json"
    dest.parent.mkdir(parents=True, exist_ok=True)
    current = load_json(dest, {"version": 1, "hooks": {}})
    hooks = current.setdefault("hooks", {})
    script_names = {spec["script"] for spec in items.values()}
    ours: list[dict] = []
    for spec in items.values():
        cursor = spec.get("cursor") or {}
        event = cursor.get("event") or "beforeShellExecution"
        if event != "beforeShellExecution":
            continue
        entry = {
            "command": command_line(spec),
            "timeout": cursor.get("timeout", spec.get("timeout", 5)),
            "failClosed": False,
        }
        matcher = cursor.get("matcher") or (spec.get("events") or {}).get("PreToolUse", {}).get("matcher")
        if matcher:
            entry["matcher"] = matcher
        ours.append(entry)
    existing = hooks.get("beforeShellExecution") or []
    hooks["beforeShellExecution"] = _strip_handlers(existing, script_names) + ours
    current["version"] = current.get("version", 1)
    dest.write_text(json.dumps(current, indent=2) + "\n")


def _claude_groups(items: dict[str, dict]) -> dict[str, list]:
    grouped: dict[str, list] = {}
    for spec in items.values():
        for event, cfg in (spec.get("events") or {}).items():
            group = {
                "hooks": [
                    {
                        "type": "command",
                        "command": command_line(spec),
                        "timeout": spec.get("timeout", 5),
                    }
                ]
            }
            matcher = (cfg or {}).get("matcher")
            if matcher:
                group["matcher"] = matcher
            grouped.setdefault(event, []).append(group)
    return grouped


def _strip_claude_event(groups: list, script_names: set[str]) -> list:
    kept = []
    for group in groups or []:
        inner = group.get("hooks") or []
        remaining = _strip_handlers(inner, script_names)
        if remaining:
            new_group = dict(group)
            new_group["hooks"] = remaining
            kept.append(new_group)
    return kept


def sync_claude(items: dict[str, dict]) -> None:
    cc = HOME / ".claude"
    dest = cc / "settings.json"
    dest.parent.mkdir(parents=True, exist_ok=True)
    current = load_json(dest, {})
    hooks = current.setdefault("hooks", {})
    script_names = {spec["script"] for spec in items.values()} | {
        "rm-guard.sh",
        "rm_guard.py",
        "sql-guard.sh",
        "sql_guard.py",
        "git-destructive-guard.sh",
        "git_destructive_guard.py",
        "docker-guard.sh",
        "docker_guard.py",
        "commit-identity-guard.sh",
        "commit_identity_guard.py",
        "ssh-prod-guard.sh",
        "ssh_prod_guard.py",
        "stockfy-guard.sh",
        "stockfy_git_flow.py",
        "stockfy_foreign_repos_guard.py",
        "protect_secrets.py",
    }
    incoming = _claude_groups(items)
    for event in set(hooks) | set(incoming):
        hooks[event] = _strip_claude_event(hooks.get(event) or [], script_names) + incoming.get(event, [])
        if not hooks[event]:
            hooks.pop(event, None)
    dest.write_text(json.dumps(current, indent=2, ensure_ascii=False) + "\n")


def sync_antigravity(items: dict[str, dict]) -> None:
    dest = HOME / ".gemini" / "config" / "hooks.json"
    dest.parent.mkdir(parents=True, exist_ok=True)
    current = load_json(dest, {})
    managed = {name for name, spec in items.items()}
    for name in list(current):
        blob = json.dumps(current.get(name) or {})
        if name in managed or _managed_command(blob):
            current.pop(name, None)
    for name, spec in items.items():
        matcher = spec.get("antigravityMatcher") or "run_command"
        events = spec.get("events") or {}
        entry: dict = {"enabled": True}
        if "PreToolUse" in events:
            entry["PreToolUse"] = [
                {
                    "matcher": matcher,
                    "hooks": [
                        {
                            "type": "command",
                            "command": command_line(spec),
                            "timeout": spec.get("timeout", 5),
                        }
                    ],
                }
            ]
        current[name] = entry
    dest.write_text(json.dumps(current, indent=2) + "\n")


def sync_gemini_cli(items: dict[str, dict]) -> None:
    dest = HOME / ".gemini" / "settings.json"
    dest.parent.mkdir(parents=True, exist_ok=True)
    current = load_json(dest, {})
    hooks = current.setdefault("hooks", {})
    script_names = {spec["script"] for spec in items.values()}
    ours = []
    for name, spec in items.items():
        if "PreToolUse" not in (spec.get("events") or {}):
            continue
        ours.append(
            {
                "matcher": spec.get("antigravityMatcher") or "*",
                "hooks": [
                    {
                        "name": name,
                        "type": "command",
                        "command": command_line(spec),
                        "timeout": int(spec.get("timeout", 5)) * 1000,
                    }
                ],
            }
        )
    hooks["BeforeTool"] = _strip_claude_event(hooks.get("BeforeTool") or [], script_names) + ours
    dest.write_text(json.dumps(current, indent=2) + "\n")


def sync_windsurf(items: dict[str, dict]) -> None:
    dest = HOME / ".codeium" / "windsurf" / "hooks.json"
    dest.parent.mkdir(parents=True, exist_ok=True)
    current = load_json(dest, {"hooks": {}})
    hooks = current.setdefault("hooks", {})
    script_names = {spec["script"] for spec in items.values()}
    by_event: dict[str, list] = {}
    for spec in items.values():
        event = spec.get("windsurfEvent") or "pre_run_command"
        by_event.setdefault(event, []).append(
            {"command": command_line(spec), "show_output": True}
        )
    for event, ours in by_event.items():
        existing = hooks.get(event) or []
        hooks[event] = _strip_handlers(existing, script_names) + ours
    dest.write_text(json.dumps(current, indent=2) + "\n")


SYNC = {
    "grok": sync_grok,
    "cursor": sync_cursor,
    "claude": sync_claude,
    "antigravity": sync_antigravity,
    "gemini": sync_gemini_cli,
    "windsurf": sync_windsurf,
}


def sync(client: str = "all") -> dict[str, dict]:
    items = catalog()
    targets = list(SYNC) if client == "all" else [client]
    for name in targets:
        SYNC[name](items)
        print(f"{name}: {len(items)} hook(s)")
    return items


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    client = args[0] if args else os.environ.get("HARNESS_HOOKS_CLIENT", "all")
    sync(client)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

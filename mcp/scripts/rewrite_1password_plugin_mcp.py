#!/usr/bin/env python3
"""Plugin 1Password do Cursor: troca `1password-mcp` nu (ENOENT no PATH do Electron) pelo wrapper absoluto."""

from __future__ import annotations

import json
from pathlib import Path

HOME = Path.home()
ROOT = Path(__file__).resolve().parents[1]
WRAPPER = ROOT / "scripts" / "run-1password-mcp"
PLUGIN_MCP_GLOB = "plugins/cache/cursor-public/1password/*/mcp.json"


def rewrite_1password_plugin_mcp(path: Path, wrapper: Path) -> bool:
    data = json.loads(path.read_text() or "{}")
    servers = data.get("mcpServers") or {}
    cfg = servers.get("1password")
    if not isinstance(cfg, dict):
        return False
    wanted = {
        "command": "bash",
        "args": [str(wrapper)],
        "env": dict(cfg.get("env") or {}),
    }
    if cfg.get("command") == wanted["command"] and cfg.get("args") == wanted["args"]:
        return False
    servers["1password"] = wanted
    data["mcpServers"] = servers
    path.write_text(json.dumps(data, indent=2) + "\n")
    return True


def rewrite_all_1password_plugin_mcp(cursor_home: Path, wrapper: Path) -> int:
    count = 0
    for path in sorted(cursor_home.glob(PLUGIN_MCP_GLOB)):
        if path.is_file() and rewrite_1password_plugin_mcp(path, wrapper):
            count += 1
    return count


def main() -> None:
    n = rewrite_all_1password_plugin_mcp(HOME / ".cursor", WRAPPER)
    print(f"1password plugin mcp.json: {n} reescrito(s)")


if __name__ == "__main__":
    main()

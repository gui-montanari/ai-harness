#!/usr/bin/env python3
"""Plugin Hostinger do Cursor: troca npx @latest (corrida ENOTEMPTY + shebang 644) por node local."""

from __future__ import annotations

import json
from pathlib import Path

HOME = Path.home()
ROOT = Path(__file__).resolve().parents[1]
WRAPPER = ROOT / "scripts" / "run-hostinger-plugin"
PLUGIN_MCP_GLOB = "plugins/cache/cursor-public/hostinger-cursor-plugin/*/mcp.json"

GROUPS = {
    "hostinger-hosting": "hosting",
    "hostinger-wordpress": "wordpress",
    "hostinger-domains": "domains",
    "hostinger-dns": "dns",
    "hostinger-billing": "billing",
    "hostinger-reach": "reach",
    "hostinger-ecommerce": "ecommerce",
    "hostinger-vps": "vps",
}


def rewrite_hostinger_plugin_mcp(path: Path, wrapper: Path) -> bool:
    data = json.loads(path.read_text() or "{}")
    servers = data.get("mcpServers") or {}
    changed = False
    for name, group in GROUPS.items():
        cfg = servers.get(name)
        if not isinstance(cfg, dict):
            continue
        wanted = {
            "command": "bash",
            "args": [str(wrapper), group],
            "env": dict(cfg.get("env") or {}),
        }
        if cfg.get("command") != wanted["command"] or cfg.get("args") != wanted["args"]:
            servers[name] = wanted
            changed = True
    if changed:
        data["mcpServers"] = servers
        path.write_text(json.dumps(data, indent=2) + "\n")
    return changed


def rewrite_all_hostinger_plugin_mcp(cursor_home: Path, wrapper: Path) -> int:
    count = 0
    for path in sorted((cursor_home).glob(PLUGIN_MCP_GLOB)):
        if path.is_file() and rewrite_hostinger_plugin_mcp(path, wrapper):
            count += 1
    return count


def main() -> None:
    n = rewrite_all_hostinger_plugin_mcp(HOME / ".cursor", WRAPPER)
    print(f"hostinger plugin mcp.json: {n} reescrito(s)")


if __name__ == "__main__":
    main()

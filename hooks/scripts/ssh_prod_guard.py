#!/usr/bin/env python3
"""Pede confirmação para comando destrutivo só em SSH/MCP de produção — nunca no Bash local."""

from __future__ import annotations

import re
from pathlib import Path

import hooklib

PROD_HOST = re.compile(
    r"(prod|production|hostinger|vps\d*|^root@)",
    re.IGNORECASE,
)
SSH_BINS = {"ssh", "scp", "sftp"}
MCP_HINT = re.compile(r"(ssh|hostinger)", re.IGNORECASE)
LOCAL_TOOLS = {
    "bash",
    "run_terminal_command",
    "shell",
    "runcommand",
}
DESTRUCTIVE = re.compile(
    r"(rm\s+-[a-zA-Z]*r[a-zA-Z]*f|rm\s+-[a-zA-Z]*f[a-zA-Z]*r"
    r"|systemctl\s+(stop|disable|mask)"
    r"|docker\s+rm\s+-f|docker\s+stop|podman\s+rm\s+-f"
    r"|kill\s+-9|\bpkill\b|\breboot\b|\bshutdown\b"
    r"|\bDROP\s+(TABLE|DATABASE|SCHEMA)\b"
    r"|DELETE\s+FROM|\bTRUNCATE\b)",
    re.IGNORECASE,
)


def _is_mcp_remote(payload: dict) -> bool:
    name = hooklib.tool_name(payload)
    if not name:
        return False
    if name.lower() in LOCAL_TOOLS:
        return False
    return bool(MCP_HINT.search(name))


def _ssh_remote_command(tokens: list[str]) -> tuple[str, str] | None:
    tokens = hooklib.skip_env_and_wrappers(tokens)
    if not tokens or Path(tokens[0]).name not in SSH_BINS:
        return None
    binary = Path(tokens[0]).name
    host = ""
    remote = ""
    i = 1
    while i < len(tokens):
        item = tokens[i]
        if item in {"-p", "-P", "-l", "-i", "-o", "-F", "-c", "-L", "-R", "-D"}:
            i += 2
            continue
        if item.startswith("-"):
            i += 1
            continue
        host = item
        rest = tokens[i + 1 :]
        remote = " ".join(rest)
        break
    if binary == "scp":
        remote = " ".join(tokens[1:])
    return host, remote


def decide(payload: dict) -> dict[str, str]:
    if _is_mcp_remote(payload):
        blob = " ".join(
            [
                hooklib.command_text(payload),
                str(hooklib.tool_input(payload)),
            ]
        )
        if DESTRUCTIVE.search(blob):
            return hooklib.confirm(
                "Comando destrutivo em sessão remota de produção. Confirme se era isso mesmo."
            )
        return hooklib.allow()

    command = hooklib.command_text(payload)
    if not command:
        return hooklib.allow()
    for tokens in hooklib.invocations(command):
        parsed = _ssh_remote_command(tokens)
        if not parsed:
            continue
        host, remote = parsed
        target = f"{host} {remote}"
        if not PROD_HOST.search(host) and not PROD_HOST.search(target):
            continue
        if DESTRUCTIVE.search(remote) or DESTRUCTIVE.search(target):
            return hooklib.confirm(
                f"Comando destrutivo via SSH em possível produção ({host or 'host'}). "
                "Confirme se era isso mesmo."
            )
    return hooklib.allow()


if __name__ == "__main__":
    raise SystemExit(hooklib.run(decide))

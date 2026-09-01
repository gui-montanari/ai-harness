#!/usr/bin/env python3
"""Recusa versionar segredo e recusa gravar chave privada no workspace."""

from __future__ import annotations

import re

import hooklib

SECRET_BASENAME = re.compile(
    r"^("
    r"\.env"
    r"|\.env\..+"
    r"|credentials\.json"
    r"|secrets\.json"
    r"|id_rsa"
    r"|id_ed25519"
    r"|.*\.(pem|p12|pfx)$"
    r"|.*(?<!\.pub)\.key$"
    r")$",
    re.IGNORECASE,
)
KEY_MATERIAL = re.compile(
    r"^("
    r"credentials\.json"
    r"|secrets\.json"
    r"|id_rsa"
    r"|id_ed25519"
    r"|.*\.(pem|p12|pfx)$"
    r"|.*(?<!\.pub)\.key$"
    r")$",
    re.IGNORECASE,
)
EXAMPLE_BASENAME = re.compile(r"\.example(\b|$)|^\.env\.example$", re.IGNORECASE)
WRITE_TOOLS = {
    "write",
    "edit",
    "strreplace",
    "search_replace",
    "notebookedit",
    "applypatch",
}


def _basename(token: str) -> str:
    return token.rstrip("/").rsplit("/", 1)[-1]


def _is_secret(token: str) -> bool:
    name = _basename(token)
    return not EXAMPLE_BASENAME.search(name) and bool(SECRET_BASENAME.match(name))


def _is_key_material(token: str) -> bool:
    name = _basename(token)
    return not EXAMPLE_BASENAME.search(name) and bool(KEY_MATERIAL.match(name))


def _secret_argv(command: str) -> list[str]:
    found: list[str] = []
    cwd = None
    for call in hooklib.git_calls(command, cwd):
        if call.subcommand not in {"add", "commit", "stage"}:
            continue
        for token in call.positionals():
            if _is_secret(token):
                found.append(token)
    return found


def decide(payload: dict) -> dict[str, str]:
    tool = hooklib.tool_name(payload).lower()
    keys = [path for path in hooklib.file_targets(payload) if _is_key_material(path)]
    if keys:
        listed = ", ".join(keys)
        return hooklib.deny(
            f"Recusei gravar chave ou credencial ({listed}). "
            "Use um secret manager ou um *.example."
        )
    if tool in WRITE_TOOLS:
        return hooklib.allow()
    secrets = _secret_argv(hooklib.command_text(payload))
    if not secrets:
        return hooklib.allow()
    listed = ", ".join(secrets)
    return hooklib.deny(
        f"Recusei versionar possível segredo ({listed}). "
        "Use secrets.example / *.example. git add . continua a depender do .gitignore."
    )


if __name__ == "__main__":
    raise SystemExit(hooklib.run(decide))

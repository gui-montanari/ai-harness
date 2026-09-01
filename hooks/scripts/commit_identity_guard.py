#!/usr/bin/env python3
"""Recusa trailer/mensagem que atribui o commit a Claude/Anthropic."""

from __future__ import annotations

from pathlib import Path

import hooklib

FORBIDDEN = (
    "noreply@anthropic",
    "co-authored-by: claude",
    "co-authored-by: anthropic",
    "generated-by: claude",
    "generated-by: anthropic",
)
MESSAGE_FLAGS = {"-m", "--message", "-F", "--file", "--trailer"}


def _messages(call: hooklib.GitCall) -> list[str]:
    texts: list[str] = []
    args = list(call.args)
    i = 0
    while i < len(args):
        item = args[i]
        flag = item.split("=", 1)[0]
        if flag not in MESSAGE_FLAGS:
            i += 1
            continue
        if "=" in item:
            value = item.split("=", 1)[1]
            i += 1
        elif i + 1 < len(args):
            value = args[i + 1]
            i += 2
        else:
            break
        if flag in {"-F", "--file"}:
            path = Path(value)
            if path.is_file() and path.stat().st_size <= 65536:
                texts.append(path.read_text(encoding="utf-8", errors="replace"))
            continue
        texts.append(value)
    return texts


def _forbidden(text: str) -> bool:
    lowered = text.lower()
    return any(token in lowered for token in FORBIDDEN)


def decide(payload: dict) -> dict[str, str]:
    command = hooklib.command_text(payload)
    if not command:
        return hooklib.allow()
    cwd = hooklib.cwd_path(payload)
    for call in hooklib.git_calls(command, cwd):
        if call.subcommand != "commit":
            continue
        for text in _messages(call):
            if _forbidden(text):
                return hooklib.deny(
                    "Recusei commit com Co-Authored-By/Generated-By Claude ou Anthropic. "
                    "Remova o trailer."
                )
    return hooklib.allow()


if __name__ == "__main__":
    raise SystemExit(hooklib.run(decide))

#!/usr/bin/env python3
"""Pede confirmação para git destrutivo (reset --hard, push -f, clean -f, discard)."""

from __future__ import annotations

import hooklib


def _reason(call: hooklib.GitCall) -> str | None:
    if call.subcommand == "reset" and call.has("--hard"):
        return "git reset --hard descarta commits e working tree."
    if call.subcommand == "push":
        forced = call.has("-f", "--force")
        leased = call.has("--force-with-lease", "--force-if-includes")
        if forced and not leased:
            return "git push --force sem --force-with-lease reescreve o remoto."
        return None
    if call.subcommand == "branch" and call.has("-D"):
        return "git branch -D apaga branch não mesclada."
    if call.subcommand in {"checkout", "restore"}:
        positionals = call.positionals()
        if positionals == (".",) or positionals == (":/",):
            return f"git {call.subcommand} . descarta todas as mudanças locais."
        return None
    if call.subcommand == "clean" and call.has("-f", "--force"):
        return "git clean -f apaga arquivos untracked."
    return None


def decide(payload: dict) -> dict[str, str]:
    command = hooklib.command_text(payload)
    if not command:
        return hooklib.allow()
    cwd = hooklib.cwd_path(payload)
    for call in hooklib.git_calls(command, cwd):
        reason = _reason(call)
        if reason:
            return hooklib.confirm(reason + " Confirme se era isso mesmo.")
    return hooklib.allow()


if __name__ == "__main__":
    raise SystemExit(hooklib.run(decide))

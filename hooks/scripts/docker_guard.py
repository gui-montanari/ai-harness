#!/usr/bin/env python3
"""Pede confirmação para apagar volume Docker/Compose, sem casar 'countdown -v'."""

from __future__ import annotations

from pathlib import Path

import hooklib

COMPOSE_VALUE = {
    "-f",
    "--file",
    "-p",
    "--project-name",
    "--env-file",
    "--profile",
    "--project-directory",
    "--progress",
}


def _skip_opts(tokens: list[str], i: int, value_opts: set[str]) -> int:
    while i < len(tokens):
        item = tokens[i]
        if item == "--":
            return i + 1
        if not item.startswith("-"):
            return i
        flag = item.split("=", 1)[0]
        if flag in value_opts and "=" not in item:
            i += 2
        else:
            i += 1
    return i


def _compose_tokens(tokens: list[str]) -> list[str] | None:
    tokens = hooklib.skip_env_and_wrappers(tokens)
    if not tokens:
        return None
    name = Path(tokens[0]).name
    if name in {"docker-compose", "podman-compose"}:
        i = _skip_opts(tokens, 1, COMPOSE_VALUE)
        return tokens[i:]
    if name in {"docker", "podman"} and len(tokens) > 1 and tokens[1] == "compose":
        i = _skip_opts(tokens, 2, COMPOSE_VALUE)
        return tokens[i:]
    return None


def _docker_tokens(tokens: list[str]) -> list[str] | None:
    tokens = hooklib.skip_env_and_wrappers(tokens)
    if not tokens or Path(tokens[0]).name not in {"docker", "podman"}:
        return None
    if len(tokens) > 1 and tokens[1] == "compose":
        return None
    return tokens[1:]


def _has_volume_flag(args: list[str]) -> bool:
    for item in args:
        if item in {"-v", "--volumes"} or item.startswith("--volumes="):
            return True
        if item.startswith("-") and not item.startswith("--") and "v" in item[1:]:
            return True
    return False


def decide(payload: dict) -> dict[str, str]:
    command = hooklib.command_text(payload)
    if not command:
        return hooklib.allow()
    for tokens in hooklib.invocations(command):
        compose = _compose_tokens(tokens)
        if compose and compose[0] == "down" and _has_volume_flag(compose[1:]):
            return hooklib.confirm(
                "compose down -v/--volumes apaga volumes. Confirme se era isso mesmo."
            )
        docker = _docker_tokens(tokens)
        if not docker:
            continue
        if docker[:2] == ["volume", "rm"] or docker[:2] == ["volume", "prune"]:
            return hooklib.confirm(
                "remoção de Docker volume é permanente. Confirme se era isso mesmo."
            )
        if docker[:2] == ["system", "prune"] and _has_volume_flag(docker[2:]):
            return hooklib.confirm(
                "docker system prune --volumes apaga volumes. Confirme se era isso mesmo."
            )
    return hooklib.allow()


if __name__ == "__main__":
    raise SystemExit(hooklib.run(decide))

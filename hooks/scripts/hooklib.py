"""Payload, argv e decisão JSON — SSOT dos guards."""

from __future__ import annotations

import json
import os
import re
import shlex
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

ALLOW = "allow"
DENY = "deny"
ASK = "ask"

_CHUNK = re.compile(r"\s*(?:&&|\|\||;)\s*")
_ENV_ASSIGN = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*=")
_WRAPPERS = {"sudo", "command", "time", "nohup", "nice", "env"}
_WRAPPER_VALUE = {"-u", "-g", "-C", "--user", "--group"}
_GIT_VALUE = {
    "-C",
    "-c",
    "--git-dir",
    "--work-tree",
    "--namespace",
    "--config-env",
    "--super-prefix",
}


def load_payload() -> dict:
    try:
        raw = sys.stdin.read()
        return json.loads(raw) if raw.strip() else {}
    except json.JSONDecodeError:
        return {}


def tool_name(payload: dict) -> str:
    return str(payload.get("toolName") or payload.get("tool_name") or "").strip()


def tool_input(payload: dict) -> dict:
    raw = payload.get("toolInput") or payload.get("tool_input") or {}
    if isinstance(raw, dict):
        return raw
    return {}


def command_text(payload: dict) -> str:
    inp = tool_input(payload)
    if inp.get("command"):
        return str(inp["command"])
    call = payload.get("toolCall") or {}
    args = call.get("args") if isinstance(call, dict) else {}
    if isinstance(args, dict) and args.get("CommandLine"):
        return str(args["CommandLine"])
    return str(payload.get("command") or "")


def cwd_path(payload: dict) -> Path:
    raw = payload.get("cwd") or os.environ.get("PWD") or "."
    return Path(str(raw)).expanduser()


def workspace_path(payload: dict) -> Path | None:
    raw = (
        payload.get("workspaceRoot")
        or payload.get("workspace_root")
        or os.environ.get("GROK_WORKSPACE_ROOT")
    )
    return Path(str(raw)).expanduser() if raw else None


def file_targets(payload: dict) -> list[str]:
    inp = tool_input(payload)
    found: list[str] = []
    for key in ("file_path", "path", "target_file", "filePath", "targetFile"):
        value = inp.get(key)
        if isinstance(value, str) and value:
            found.append(value)
        elif isinstance(value, list):
            found.extend(str(item) for item in value if item)
    return found


def chunks(command: str) -> list[str]:
    return [part.strip() for part in _CHUNK.split(command) if part.strip()]


def argv(chunk: str) -> list[str]:
    try:
        return shlex.split(chunk)
    except ValueError:
        return chunk.split()


def invocations(command: str) -> list[list[str]]:
    return [argv(part) for part in chunks(command)]


def skip_env_and_wrappers(tokens: list[str]) -> list[str]:
    i = 0
    while i < len(tokens) and _ENV_ASSIGN.match(tokens[i] or ""):
        i += 1
    while i < len(tokens) and Path(tokens[i]).name in _WRAPPERS:
        i += 1
        while i < len(tokens) and tokens[i].startswith("-"):
            flag = tokens[i].split("=", 1)[0]
            if flag in _WRAPPER_VALUE and "=" not in tokens[i]:
                i += 2
            else:
                i += 1
    return tokens[i:]


def resolve_path(token: str, cwd: Path) -> Path:
    expanded = os.path.expandvars(os.path.expanduser(token))
    path = Path(expanded)
    if not path.is_absolute():
        path = cwd / path
    try:
        return path.resolve(strict=False)
    except OSError:
        return path


def supports_ask() -> bool:
    return bool(os.environ.get("GROK_HOOK_EVENT"))


def allow() -> dict[str, str]:
    return {"decision": ALLOW}


def deny(reason: str) -> dict[str, str]:
    return {"decision": DENY, "reason": reason}


def confirm(reason: str) -> dict[str, str]:
    if supports_ask():
        return {"decision": ASK, "reason": reason}
    return deny(reason)


def emit(decision: dict[str, str]) -> int:
    json.dump(decision, sys.stdout)
    sys.stdout.write("\n")
    if decision.get("decision") == DENY:
        print(decision.get("reason", ""), file=sys.stderr)
        return 2
    return 0


def run(decide: Callable[[dict], dict[str, str]]) -> int:
    return emit(decide(load_payload()))


@dataclass(frozen=True)
class GitCall:
    subcommand: str
    args: tuple[str, ...]
    repo: Path | None

    def has(self, *opts: str) -> bool:
        exact = set(opts)
        shorts = {opt[1:] for opt in opts if len(opt) == 2 and opt.startswith("-")}
        longs = {opt for opt in opts if opt.startswith("--")}
        after_dd = False
        for item in self.args:
            if item == "--":
                after_dd = True
                continue
            if after_dd:
                continue
            if item in exact:
                return True
            if item.startswith("--") and item.split("=", 1)[0] in longs:
                return True
            if item.startswith("-") and not item.startswith("--"):
                if any(letter in item[1:] for letter in shorts):
                    return True
        return False

    def positionals(self) -> tuple[str, ...]:
        found: list[str] = []
        after_dd = False
        for item in self.args:
            if item == "--":
                after_dd = True
                continue
            if after_dd or not item.startswith("-"):
                found.append(item)
        return tuple(found)


def parse_git_argv(tokens: list[str], cwd: Path | None) -> GitCall | None:
    repo = cwd
    i = 1
    while i < len(tokens):
        item = tokens[i]
        if item == "--":
            i += 1
            break
        if item == "-C" and i + 1 < len(tokens):
            repo = resolve_path(tokens[i + 1], repo or Path("."))
            i += 2
            continue
        if item.startswith("-C") and len(item) > 2 and not item.startswith("--"):
            repo = resolve_path(item[2:], repo or Path("."))
            i += 1
            continue
        flag = item.split("=", 1)[0]
        if flag in _GIT_VALUE and "=" not in item and i + 1 < len(tokens):
            i += 2
            continue
        if item.startswith("-"):
            i += 1
            continue
        break
    if i >= len(tokens):
        return None
    return GitCall(tokens[i], tuple(tokens[i + 1 :]), repo)


def git_calls(command: str, cwd: Path | None = None) -> list[GitCall]:
    found: list[GitCall] = []
    for tokens in invocations(command):
        tokens = skip_env_and_wrappers(tokens)
        if not tokens or Path(tokens[0]).name != "git":
            continue
        call = parse_git_argv(tokens, cwd)
        if call:
            found.append(call)
    return found

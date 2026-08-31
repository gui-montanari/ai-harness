#!/usr/bin/env python3
"""Executa gates declarados e grava evidência reproduzível para os audits."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shlex
import subprocess
import time
from pathlib import Path

from verify_audit import workspace_fingerprint

SECRET_PATTERNS = (
    re.compile(r"(?i)(authorization:\s*bearer\s+)[^\s]+"),
    re.compile(r"(?i)((?:password|secret|token|api[_-]?key)\s*[=:]\s*)[^\s]+"),
    re.compile(r"\beyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\b"),
)


def redact(value: str) -> str:
    for pattern in SECRET_PATTERNS:
        value = pattern.sub(r"\1[REDACTED]" if pattern.groups else "[REDACTED]", value)
    return value


def parse_check(raw: str) -> tuple[str, str]:
    if "::" not in raw:
        raise argparse.ArgumentTypeError("use NAME::COMMAND")
    name, command = (part.strip() for part in raw.split("::", 1))
    if not name or not command:
        raise argparse.ArgumentTypeError("NAME e COMMAND são obrigatórios")
    return name, command


def git_commit(root: Path) -> str:
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=root, text=True, capture_output=True, check=False
    )
    return result.stdout.strip() if result.returncode == 0 else "unknown"


def run(root: Path, name: str, command: str, timeout: int) -> dict:
    started = time.monotonic()
    try:
        result = subprocess.run(
            shlex.split(command),
            cwd=root,
            text=True,
            capture_output=True,
            timeout=timeout,
            check=False,
        )
        output = redact((result.stdout + "\n" + result.stderr).strip())
        exit_code = result.returncode
    except (OSError, subprocess.TimeoutExpired) as exc:
        output = redact(str(exc))
        exit_code = 124 if isinstance(exc, subprocess.TimeoutExpired) else 127
    encoded = output.encode("utf-8", errors="replace")
    return {
        "name": name,
        "command": command,
        "required": True,
        "exit_code": exit_code,
        "duration_seconds": round(time.monotonic() - started, 3),
        "output_sha256": hashlib.sha256(encoded).hexdigest(),
        "output_tail": "\n".join(output.splitlines()[-40:]),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--check", action="append", type=parse_check, required=True)
    parser.add_argument("--timeout", type=int, default=1800)
    args = parser.parse_args()
    root = args.root.resolve()
    evidence = {
        "schema_version": 1,
        "root": str(root),
        "commit": git_commit(root),
        "working_tree_sha256": workspace_fingerprint(root),
        "commands": [run(root, name, command, args.timeout) for name, command in args.check],
        "authorities": [],
        "inventory_dispositions": [],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(evidence, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    raise SystemExit(1 if any(item["exit_code"] for item in evidence["commands"]) else 0)


if __name__ == "__main__":
    main()

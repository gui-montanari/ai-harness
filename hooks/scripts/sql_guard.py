#!/usr/bin/env python3
"""Pede confirmação para SQL destrutivo só em cliente de banco (não em commit message)."""

from __future__ import annotations

import re
from pathlib import Path

import hooklib

DB_CLIS = {
    "psql",
    "mysql",
    "mysqlsh",
    "sqlite3",
    "sqlcmd",
    "pgcli",
    "cockroach",
}
INLINE_FLAGS = {"-c", "--command", "-e", "--execute", "-Q", "--query"}
DROP = re.compile(
    r"\bDROP\s+(TABLE|DATABASE|SCHEMA|INDEX|VIEW|ROLE|USER)\b", re.IGNORECASE
)
TRUNCATE = re.compile(r"\bTRUNCATE\b", re.IGNORECASE)
DELETE = re.compile(r"\bDELETE\s+FROM\b", re.IGNORECASE)
UPDATE = re.compile(r"\bUPDATE\s+\S+\s+SET\b", re.IGNORECASE)
WHERE = re.compile(r"\bWHERE\b", re.IGNORECASE)
COMMENT = re.compile(r"/\*.*?\*/|--[^\n]*", re.DOTALL)


def _inline_sql(tokens: list[str]) -> str | None:
    sql: list[str] = []
    i = 0
    while i < len(tokens):
        item = tokens[i]
        flag = item.split("=", 1)[0]
        if flag in INLINE_FLAGS:
            if "=" in item:
                sql.append(item.split("=", 1)[1])
            elif i + 1 < len(tokens):
                sql.append(tokens[i + 1])
                i += 2
                continue
        i += 1
    return "\n".join(sql) if sql else None


def _find_cli(tokens: list[str]) -> tuple[str, list[str]] | None:
    tokens = hooklib.skip_env_and_wrappers(tokens)
    for i, item in enumerate(tokens):
        name = Path(item).name.lower()
        if name in DB_CLIS:
            return name, tokens[i + 1 :]
    return None


def _statements(sql: str) -> list[str]:
    cleaned = COMMENT.sub(" ", sql)
    return [part.strip() for part in cleaned.split(";") if part.strip()]


def _destructive(sql: str) -> str | None:
    for stmt in _statements(sql):
        if DROP.search(stmt) or TRUNCATE.search(stmt):
            return stmt
        if (DELETE.search(stmt) or UPDATE.search(stmt)) and not WHERE.search(stmt):
            return stmt
    return None


def decide(payload: dict) -> dict[str, str]:
    command = hooklib.command_text(payload)
    if not command:
        return hooklib.allow()
    for tokens in hooklib.invocations(command):
        found = _find_cli(tokens)
        if not found:
            continue
        _, rest = found
        sql = _inline_sql(rest)
        if not sql:
            continue
        hit = _destructive(sql)
        if hit:
            return hooklib.confirm(
                f"SQL destrutivo no cliente de banco ({hit[:120]}). Confirme antes de executar."
            )
    return hooklib.allow()


if __name__ == "__main__":
    raise SystemExit(hooklib.run(decide))

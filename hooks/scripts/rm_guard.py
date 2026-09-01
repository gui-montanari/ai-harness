#!/usr/bin/env python3
"""Pede confirmação para rm recursivo+forçado em raiz, home, workspace ou sistema."""

from __future__ import annotations

from pathlib import Path

import hooklib

EXACT = {Path("/"), Path("/home")}
SYSTEM_PREFIX = tuple(
    Path(p)
    for p in (
        "/etc",
        "/usr",
        "/bin",
        "/sbin",
        "/boot",
        "/root",
        "/var",
        "/opt",
        "/dev",
        "/proc",
        "/sys",
        "/lib",
        "/lib64",
    )
)


def _rm_args(tokens: list[str]) -> tuple[bool, bool, list[str]] | None:
    tokens = hooklib.skip_env_and_wrappers(tokens)
    if not tokens or Path(tokens[0]).name != "rm":
        return None
    recursive = False
    force = False
    targets: list[str] = []
    after_dd = False
    for item in tokens[1:]:
        if after_dd or item == "--":
            if item == "--":
                after_dd = True
                continue
            targets.append(item)
            continue
        if item.startswith("-") and not item.startswith("--"):
            letters = item[1:]
            recursive = recursive or ("r" in letters.lower())
            force = force or ("f" in letters)
            continue
        if item in {"--recursive", "--force"}:
            recursive = recursive or item == "--recursive"
            force = force or item == "--force"
            continue
        targets.append(item)
    return recursive, force, targets


def _under_or_equal(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return path == root


def _is_critical(target: Path, home: Path, workspace: Path | None) -> bool:
    if target in EXACT:
        return True
    if target == home or _under_or_equal(home, target):
        return True
    if workspace is not None and (
        target == workspace or _under_or_equal(workspace, target)
    ):
        return True
    return any(_under_or_equal(target, root) for root in SYSTEM_PREFIX)


def _dangerous_token(
    token: str, cwd: Path, home: Path, workspace: Path | None
) -> bool:
    if token in {"*", "./*", "./**"}:
        return _is_critical(cwd, home, workspace)
    if token in {".", ".."}:
        path = cwd if token == "." else cwd.parent
        return _is_critical(path, home, workspace)
    return _is_critical(hooklib.resolve_path(token, cwd), home, workspace)


def decide(
    payload: dict,
    *,
    home: Path | None = None,
    workspace: Path | None = None,
) -> dict[str, str]:
    command = hooklib.command_text(payload)
    if not command:
        return hooklib.allow()
    cwd = hooklib.cwd_path(payload)
    home = home or Path.home()
    workspace = workspace if workspace is not None else hooklib.workspace_path(payload)
    hits: list[str] = []
    for tokens in hooklib.invocations(command):
        parsed = _rm_args(tokens)
        if not parsed:
            continue
        recursive, force, targets = parsed
        if not (recursive and force):
            continue
        for token in targets:
            if _dangerous_token(token, cwd, home, workspace):
                hits.append(token)
    if not hits:
        return hooklib.allow()
    listed = ", ".join(hits)
    return hooklib.confirm(
        f"rm recursivo em caminho crítico ({listed}). Confirme se era isso mesmo."
    )


if __name__ == "__main__":
    raise SystemExit(hooklib.run(decide))

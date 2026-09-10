"""Selecionar worktrees mergeadas para sair do disco."""

from __future__ import annotations

from pathlib import Path

from ledger import PROTECTED, ActivityRow, Worktree


def is_inside(tree_path: str, cwd: str) -> bool:
    tree = Path(tree_path).resolve()
    here = Path(cwd).resolve()
    try:
        here.relative_to(tree)
    except ValueError:
        return False
    return True


def prune_candidates(
    trees: list[Worktree],
    rows: list[ActivityRow],
    *,
    cwd: str,
    main_path: str,
) -> list[Worktree]:
    allowed = {row.branch for row in rows if row.estado == "mergeada"}
    main = Path(main_path).resolve()
    out: list[Worktree] = []
    for tree in trees:
        if tree.branch in PROTECTED:
            continue
        resolved = Path(tree.path).resolve()
        if resolved == main:
            continue
        if is_inside(tree.path, cwd):
            continue
        if tree.branch in allowed:
            out.append(tree)
    return out

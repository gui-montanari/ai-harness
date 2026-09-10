#!/usr/bin/env python3
"""CLI do índice local de atividades git."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

from atividades import parse_ledger, render_ledger, upsert_section
from ledger import (
    ActivityRow,
    PullRequest,
    Worktree,
    classify_estado,
    find_existing_activity,
    infer_worktrees_dir,
    match_prs,
    parse_gh_prs,
    parse_worktree_porcelain,
    reconcile,
    row_from_worktree,
)
from prune import prune_candidates
from names import (
    activity_stamp,
    branch_name,
    delivery_branch,
    parse_activity_branch,
    worktree_folder,
)

__all__ = [
    "ActivityRow",
    "PullRequest",
    "Worktree",
    "activity_stamp",
    "branch_name",
    "classify_estado",
    "delivery_branch",
    "find_existing_activity",
    "parse_activity_branch",
    "parse_ledger",
    "parse_worktree_porcelain",
    "match_prs",
    "prune_candidates",
    "reconcile",
    "render_ledger",
    "upsert_section",
    "worktree_folder",
]


def _run(argv: list[str]) -> str:
    result = subprocess.run(argv, check=True, capture_output=True, text=True)
    return result.stdout


def load_prs() -> list[PullRequest]:
    try:
        raw = _run(
            [
                "gh",
                "pr",
                "list",
                "--state",
                "all",
                "--limit",
                "50",
                "--json",
                "number,url,state,baseRefName,headRefName,mergedAt",
            ]
        )
    except (FileNotFoundError, subprocess.CalledProcessError):
        return []
    return parse_gh_prs(json.loads(raw or "[]"))


def _is_dirty(path: str) -> bool:
    try:
        return bool(_run(["git", "-C", path, "status", "--porcelain"]).strip())
    except subprocess.CalledProcessError:
        return True


def _remove_worktree(path: str) -> None:
    _run(["git", "worktree", "remove", path])


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Reconciliar ATIVIDADES.md")
    parser.add_argument("--check-slug", dest="slug")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument(
        "--prune",
        action="store_true",
        help="remover worktrees mergeadas do disco",
    )
    args = parser.parse_args(argv)
    porcelain = _run(["git", "worktree", "list", "--porcelain"])
    trees = parse_worktree_porcelain(porcelain)
    if args.slug:
        found = find_existing_activity(trees, slug=args.slug)
        if found is None:
            return 1
        print(found.path)
        return 0
    repo = Path(trees[0].path).name if trees else Path.cwd().name
    main_path = trees[0].path if trees else str(Path.cwd())
    prs = load_prs()
    live = [
        row
        for tree in trees
        if (row := row_from_worktree(repo, tree, prs)) is not None
    ]
    worktrees_dir = infer_worktrees_dir(trees)
    path = worktrees_dir / "ATIVIDADES.md"
    existing_text = path.read_text(encoding="utf-8") if path.is_file() else ""
    existing_rows = parse_ledger(existing_text).get(repo, [])
    rows = reconcile(existing_rows, live, prs)
    if args.prune:
        for tree in prune_candidates(
            trees, rows, cwd=str(Path.cwd()), main_path=main_path
        ):
            if _is_dirty(tree.path):
                print(f"# skip dirty {tree.path}", file=sys.stderr)
                continue
            if args.dry_run:
                print(f"# would remove {tree.path}", file=sys.stderr)
                continue
            _remove_worktree(tree.path)
            print(f"# removed {tree.path}", file=sys.stderr)
        if not args.dry_run:
            try:
                _run(["git", "worktree", "prune"])
            except subprocess.CalledProcessError:
                pass
            porcelain = _run(["git", "worktree", "list", "--porcelain"])
            trees = parse_worktree_porcelain(porcelain)
            live = [
                row
                for tree in trees
                if (row := row_from_worktree(repo, tree, prs)) is not None
            ]
            existing_text = path.read_text(encoding="utf-8") if path.is_file() else ""
            existing_rows = parse_ledger(existing_text).get(repo, [])
            rows = reconcile(existing_rows, live, prs)
    updated = datetime.now().strftime("%Y-%m-%d %H:%M")
    incoming = render_ledger(repo, rows, updated=updated)
    text = upsert_section(existing_text, repo, incoming)
    if not args.dry_run:
        worktrees_dir.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    sys.stdout.write(text)
    if not args.dry_run:
        print(f"# wrote {path}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

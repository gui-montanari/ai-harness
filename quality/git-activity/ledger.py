"""Ledger local de atividades: worktrees, PRs e ATIVIDADES.md."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from names import delivery_heads_for, parse_activity_branch

PROTECTED = {"main", "master", "develop", ""}
HEADERS = (
    "pasta",
    "kind",
    "slug",
    "branch",
    "sha",
    "PR produção",
    "merge produção",
    "PR develop",
    "merge develop",
    "estado",
)
PREAMBLE = (
    "# Atividades\n\n"
    "Gerado por `quality/git-activity/status.py`. Não editar à mão.\n"
)


@dataclass(frozen=True)
class Worktree:
    path: str
    sha: str
    branch: str


@dataclass(frozen=True)
class PullRequest:
    number: int
    url: str
    state: str
    base: str
    head: str
    merged: bool


@dataclass(frozen=True)
class ActivityRow:
    repo: str
    pasta: str
    kind: str
    slug: str
    branch: str
    sha: str
    pr_prod: str
    merge_prod: str
    pr_develop: str
    merge_develop: str
    estado: str


def parse_worktree_porcelain(text: str) -> list[Worktree]:
    trees: list[Worktree] = []
    path = sha = branch = ""

    def flush() -> None:
        nonlocal path, sha, branch
        if path:
            trees.append(Worktree(path=path, sha=sha, branch=branch))
        path = sha = branch = ""

    for line in text.splitlines():
        if not line.strip():
            flush()
            continue
        if line.startswith("worktree "):
            if path:
                flush()
            path = line[len("worktree ") :]
        elif line.startswith("HEAD "):
            sha = line[len("HEAD ") :]
        elif line.startswith("branch "):
            branch = line[len("branch ") :].removeprefix("refs/heads/")
    flush()
    return trees


def find_existing_activity(trees: list[Worktree], *, slug: str) -> Worktree | None:
    for tree in trees:
        if tree.branch in PROTECTED:
            continue
        parsed = parse_activity_branch(tree.branch)
        if parsed and parsed["kind"] == "delivery":
            continue
        if parsed and parsed["slug"] == slug:
            return tree
        tail = tree.branch.rsplit("/", 1)[-1]
        if parsed is None and (tail == slug or tail.endswith(f"-{slug}")):
            return tree
    return None


def classify_estado(
    *,
    has_worktree: bool,
    pr_prod: PullRequest | None,
    pr_develop: PullRequest | None,
) -> str:
    open_pr = (pr_prod is not None and not pr_prod.merged) or (
        pr_develop is not None and not pr_develop.merged
    )
    merged = bool(pr_prod and pr_prod.merged) or bool(pr_develop and pr_develop.merged)
    if not has_worktree:
        return "podada"
    if open_pr:
        return "pr-aberta"
    if merged:
        return "mergeada"
    return "aberta"


def match_prs(
    prs: list[PullRequest], branch: str
) -> tuple[PullRequest | None, PullRequest | None]:
    parsed = parse_activity_branch(branch)
    prod = develop = None
    want_prod, want_dev = delivery_heads_for(branch)
    for pr in prs:
        if want_prod and pr.head == want_prod:
            prod = pr
        elif want_dev and pr.head == want_dev:
            develop = pr
        elif pr.head == branch:
            if parsed and parsed["kind"] == "delivery" and parsed["develop"]:
                develop = develop or pr
            else:
                prod = prod or pr
    return prod, develop


def _pr_cells(pr: PullRequest | None) -> tuple[str, str]:
    if pr is None:
        return "—", "—"
    return pr.url, "sim" if pr.merged else "não"


def _short_sha(sha: str) -> str:
    return sha[:7] if sha else "—"


def row_from_worktree(
    repo: str, tree: Worktree, prs: list[PullRequest]
) -> ActivityRow | None:
    if tree.branch in PROTECTED:
        return None
    parsed = parse_activity_branch(tree.branch) or {}
    kind = parsed.get("kind") or tree.branch.split("/", 1)[0]
    slug = parsed.get("slug") or tree.branch.split("/", 1)[-1]
    pr_prod, pr_dev = match_prs(prs, tree.branch)
    url_p, merge_p = _pr_cells(pr_prod)
    url_d, merge_d = _pr_cells(pr_dev)
    return ActivityRow(
        repo=repo,
        pasta=Path(tree.path).name,
        kind=kind,
        slug=slug,
        branch=tree.branch,
        sha=_short_sha(tree.sha),
        pr_prod=url_p,
        merge_prod=merge_p,
        pr_develop=url_d,
        merge_develop=merge_d,
        estado=classify_estado(has_worktree=True, pr_prod=pr_prod, pr_develop=pr_dev),
    )


def reconcile(
    existing: list[ActivityRow],
    live: list[ActivityRow],
    prs: list[PullRequest],
) -> list[ActivityRow]:
    live_branches = {row.branch for row in live}
    out = list(live)
    for old in existing:
        if old.branch in live_branches:
            continue
        pr_prod, pr_dev = match_prs(prs, old.branch)
        url_p, merge_p = _pr_cells(pr_prod)
        url_d, merge_d = _pr_cells(pr_dev)
        if pr_prod is None:
            url_p, merge_p = old.pr_prod, old.merge_prod
        if pr_dev is None:
            url_d, merge_d = old.pr_develop, old.merge_develop
        out.append(
            ActivityRow(
                repo=old.repo,
                pasta=old.pasta,
                kind=old.kind,
                slug=old.slug,
                branch=old.branch,
                sha=old.sha,
                pr_prod=url_p,
                merge_prod=merge_p,
                pr_develop=url_d,
                merge_develop=merge_d,
                estado=classify_estado(
                    has_worktree=False, pr_prod=pr_prod, pr_develop=pr_dev
                ),
            )
        )
    return out


def infer_worktrees_dir(trees: list[Worktree]) -> Path:
    if not trees:
        return Path.cwd().parent / "worktrees"
    main = Path(trees[0].path)
    extras = [Path(tree.path) for tree in trees[1:]]
    if extras:
        parent = extras[0].parent
        if all(path.parent == parent for path in extras):
            return parent
        return Path(min((str(path.parent) for path in extras), key=len))
    return main.parent / "worktrees"


def parse_gh_prs(payload: list[dict]) -> list[PullRequest]:
    rows: list[PullRequest] = []
    for item in payload:
        state = str(item.get("state") or "")
        merged = state == "MERGED" or bool(item.get("mergedAt"))
        rows.append(
            PullRequest(
                number=int(item.get("number") or 0),
                url=str(item.get("url") or ""),
                state=state,
                base=str(item.get("baseRefName") or ""),
                head=str(item.get("headRefName") or ""),
                merged=merged,
            )
        )
    return rows

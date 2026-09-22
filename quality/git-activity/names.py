"""Nomes canônicos de branch e pasta da atividade git."""

from __future__ import annotations

import re
from datetime import datetime

KINDS = ("feature", "bugfix", "delivery")
STAMP_RE = re.compile(r"^\d{8}-\d{4}$")
SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
MARKERS = ("not-delivery", "delivered-dev", "delivered")
FEATURE_BRANCH_RE = re.compile(r"^(feature|bugfix)/(\d{8}-\d{4})-(.+)$")
DELIVERY_BRANCH_RE = re.compile(r"^delivery/(\d{8}-\d{4})-(.+)$")


def activity_stamp(when: datetime) -> str:
    return when.strftime("%Y%m%d-%H%M")


def _validate(kind: str, stamp: str, slug: str) -> None:
    if kind not in KINDS:
        raise ValueError(f"kind inválido: {kind}")
    if not STAMP_RE.match(stamp):
        raise ValueError(f"stamp inválido: {stamp}")
    if not SLUG_RE.match(slug):
        raise ValueError(f"slug inválido: {slug}")


def branch_name(kind: str, stamp: str, slug: str) -> str:
    _validate(kind, stamp, slug)
    return f"{kind}/{stamp}-{slug}/not-delivery"


def delivery_branch(stamp: str, slug: str, *, develop: bool = False) -> str:
    _validate("delivery", stamp, slug)
    base = f"delivery/{stamp}-{slug}"
    return f"{base}-develop" if develop else base


def worktree_folder(
    *, stamp: str, kind: str, slug: str, repo: str | None = None
) -> str:
    _validate(kind, stamp, slug)
    if repo:
        return f"{stamp}-{repo}-{kind}-{slug}"
    return f"{stamp}-{kind}-{slug}"


def split_marker(branch: str) -> tuple[str, str]:
    for marker in MARKERS:
        suffix = f"/{marker}"
        if branch.endswith(suffix):
            return branch[: -len(suffix)], marker
    return branch, ""


def parse_activity_branch(branch: str) -> dict | None:
    branch, _marker = split_marker(branch)
    match = FEATURE_BRANCH_RE.match(branch)
    if match:
        return {
            "kind": match.group(1),
            "stamp": match.group(2),
            "slug": match.group(3),
            "develop": False,
        }
    match = DELIVERY_BRANCH_RE.match(branch)
    if not match:
        return None
    rest = match.group(2)
    develop = rest.endswith("-develop")
    slug = rest[: -len("-develop")] if develop else rest
    return {
        "kind": "delivery",
        "stamp": match.group(1),
        "slug": slug,
        "develop": develop,
    }


def delivery_heads_for(branch: str) -> tuple[str, str]:
    branch, _marker = split_marker(branch)
    parsed = parse_activity_branch(branch)
    if parsed:
        base = f"delivery/{parsed['stamp']}-{parsed['slug']}"
        return base, f"{base}-develop"
    _, sep, rest = branch.partition("/")
    if not sep or not rest:
        return "", ""
    if branch.startswith("delivery/"):
        if rest.endswith("-develop"):
            return f"delivery/{rest[: -len('-develop')]}", branch
        return branch, f"{branch}-develop"
    return f"delivery/{rest}", f"delivery/{rest}-develop"

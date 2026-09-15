#!/usr/bin/env python3
"""Eval estrutural e de roteamento do catálogo de skills (stdlib)."""

from __future__ import annotations

import argparse
import json
import math
import re
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

PONTE_FOLDERS = frozenset(
    {
        "oauth-connectors",
        "langgraph-agents",
        "make-scenarios",
        "channel-evolution",
    }
)
HEADING_QUANDO = "## Quando não usar"
HEADING_DESCULPAS = "## Desculpas que não valem"
HEADING_CONFERENCIA = "## Conferência"
NAME_RE = re.compile(r"^name:\s*(\S+)\s*$", re.M)
TOKEN_RE = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*", re.I)
STOP = {
    "a", "an", "the", "and", "or", "of", "to", "for", "in", "on", "at", "by",
    "is", "are", "be", "as", "with", "from", "this", "that", "when", "use",
    "using", "also", "user", "mentions", "run", "runs", "they", "their",
    "de", "da", "do", "das", "dos", "em", "um", "uma", "os", "as", "para",
    "com", "nao", "não", "que", "se", "no", "na", "por", "ao", "à", "e",
    "o", "not", "skill", "skills",
}

CASES_PATH = Path("evals") / "cases.json"


class CatalogEvalError(ValueError):
    """Frontmatter ou cases inválidos."""


@dataclass(frozen=True)
class Skill:
    name: str
    folder: str
    path: Path
    description: str
    body: str
    is_ponte: bool


@dataclass(frozen=True)
class Ranked:
    name: str
    score: float


@dataclass(frozen=True)
class Trigger:
    prompt: str
    top_k: int = 1
    owner: str | None = None


@dataclass(frozen=True)
class CaseSpec:
    positive: tuple[Trigger, ...]
    negative: tuple[Trigger, ...]


def parse_frontmatter(text: str) -> tuple[dict[str, str], str]:
    if not text.startswith("---"):
        raise CatalogEvalError("SKILL.md sem frontmatter YAML")
    rest = text[3:]
    end = rest.find("\n---")
    if end < 0:
        raise CatalogEvalError("frontmatter sem fechamento")
    raw, body = rest[:end], rest[end + 4 :]
    meta: dict[str, str] = {}
    key: str | None = None
    folded: list[str] = []
    for line in raw.splitlines():
        if key and (line.startswith("  ") or line.startswith("\t")):
            folded.append(line.strip())
            continue
        if key:
            meta[key] = " ".join(folded).strip()
            key = None
            folded = []
        match = NAME_RE.match(line)
        if match:
            meta["name"] = match.group(1)
            continue
        if line.startswith("description:"):
            tail = line.split(":", 1)[1].strip()
            if tail in {">", "|", ""}:
                key = "description"
                folded = []
            else:
                meta["description"] = tail.strip("\"'")
    if key:
        meta[key] = " ".join(folded).strip()
    if "name" not in meta or "description" not in meta:
        raise CatalogEvalError("frontmatter sem name ou description")
    return meta, body.lstrip()


def discover_skills(root: Path) -> list[Skill]:
    skills: list[Skill] = []
    found = [
        path
        for path in root.rglob("SKILL.md")
        if "node_modules" not in path.parts
    ]
    for path in sorted(found):
        text = path.read_text(encoding="utf-8")
        meta, body = parse_frontmatter(text)
        skills.append(
            Skill(
                name=meta["name"],
                folder=path.parent.name,
                path=path,
                description=meta["description"],
                body=body,
                is_ponte=path.parent.name in PONTE_FOLDERS,
            )
        )
    return skills


def structural_errors(skills: list[Skill]) -> list[str]:
    errors: list[str] = []
    for skill in skills:
        loc = str(skill.path)
        if skill.name != skill.folder:
            errors.append(f"{loc}: name={skill.name!r} ≠ pasta {skill.folder!r}")
        if HEADING_CONFERENCIA not in skill.body:
            errors.append(f"{loc}: falta {HEADING_CONFERENCIA}")
        if skill.is_ponte:
            continue
        if HEADING_QUANDO not in skill.body:
            errors.append(f"{loc}: execução sem {HEADING_QUANDO}")
        if HEADING_DESCULPAS not in skill.body:
            errors.append(f"{loc}: execução sem {HEADING_DESCULPAS}")
    return errors


def _tokens(text: str) -> list[str]:
    return [t.lower() for t in TOKEN_RE.findall(text) if t.lower() not in STOP and len(t) > 1]


def _inclusion_exclusion(description: str) -> tuple[str, str]:
    parts = re.split(r"(?i)(?:^|[.])\s*(?:not|não)\b", description, maxsplit=1)
    inclusion = parts[0]
    exclusion = parts[1] if len(parts) > 1 else ""
    return inclusion, exclusion


def _bow(text: str) -> Counter[str]:
    toks = _tokens(text)
    bag: Counter[str] = Counter(toks)
    bag.update(f"{a}_{b}" for a, b in zip(toks, toks[1:]))
    return bag


def _dot(a: Counter[str], b: Counter[str]) -> float:
    return sum(a[k] * b[k] for k in a.keys() & b.keys())


def _cosine(a: Counter[str], b: Counter[str]) -> float:
    denom = math.sqrt(_dot(a, a) * _dot(b, b))
    if denom == 0:
        return 0.0
    return _dot(a, b) / denom


def rank_prompt(prompt: str, skills: list[Skill]) -> list[Ranked]:
    query = _bow(prompt)
    prompt_l = prompt.lower()
    ranked: list[Ranked] = []
    for skill in skills:
        inclusion, exclusion = _inclusion_exclusion(skill.description)
        score = _cosine(query, _bow(inclusion + " " + skill.name))
        if exclusion:
            score -= 0.35 * _cosine(query, _bow(exclusion))
        if skill.name in prompt_l or f"/{skill.name}" in prompt_l:
            score += 0.5
        ranked.append(Ranked(name=skill.name, score=score))
    ranked.sort(key=lambda r: r.score, reverse=True)
    return ranked


def collisions(skills: list[Skill], fail_at: float = 0.75) -> list[str]:
    hits: list[str] = []
    bags = {s.name: _bow(_inclusion_exclusion(s.description)[0]) for s in skills}
    names = [s.name for s in skills]
    for i, left in enumerate(names):
        for right in names[i + 1 :]:
            sim = _cosine(bags[left], bags[right])
            if sim >= fail_at:
                hits.append(f"{left} × {right}: {sim:.2f}")
    return hits


def load_cases(root: Path) -> dict[str, CaseSpec]:
    path = root / "quality" / "skills-audit" / CASES_PATH
    if not path.is_file():
        raise CatalogEvalError(f"falta {path}")
    raw = json.loads(path.read_text(encoding="utf-8"))
    out: dict[str, CaseSpec] = {}
    for name, spec in raw.items():
        pos = tuple(
            Trigger(prompt=p["prompt"], top_k=int(p.get("top_k", 1)))
            for p in spec["positive"]
        )
        neg = tuple(
            Trigger(prompt=n["prompt"], owner=n["owner"])
            for n in spec["negative"]
        )
        out[name] = CaseSpec(positive=pos, negative=neg)
    return out


def evaluate_triggers(
    skills: list[Skill], cases: dict[str, CaseSpec]
) -> list[str]:
    by_name = {s.name: s for s in skills}
    failures: list[str] = []
    for name, spec in cases.items():
        if name not in by_name:
            failures.append(f"case {name}: skill ausente")
            continue
        for trigger in spec.positive:
            ranked = rank_prompt(trigger.prompt, skills)
            top = [r.name for r in ranked[: trigger.top_k]]
            if name not in top:
                failures.append(
                    f"{name} positivo fora do top-{trigger.top_k}: "
                    f"{trigger.prompt!r} → {[r.name for r in ranked[:3]]}"
                )
        for trigger in spec.negative:
            owner = trigger.owner or ""
            ranked = rank_prompt(trigger.prompt, skills)
            names = [r.name for r in ranked]
            if owner not in by_name:
                failures.append(f"{name} negativo: owner {owner} ausente")
                continue
            if names.index(owner) >= names.index(name):
                failures.append(
                    f"{name} negativo: {owner} não supera {name} em "
                    f"{trigger.prompt!r} → {names[:3]}"
                )
    return failures


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Eval do catálogo de skills")
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parents[2],
    )
    args = parser.parse_args(argv)
    skills = discover_skills(args.root)
    errors = structural_errors(skills)
    hits = collisions(skills)
    errors.extend(f"colisão {h}" for h in hits)
    cases = load_cases(args.root)
    execution = {s.name for s in skills if not s.is_ponte}
    missing = sorted(execution - set(cases))
    extra = sorted(set(cases) - {s.name for s in skills})
    if missing:
        errors.append(f"cases sem skill de execução: {missing}")
    if extra:
        errors.append(f"cases órfãos: {extra}")
    errors.extend(evaluate_triggers(skills, cases))
    if errors:
        sys.stderr.write("\n".join(errors) + "\n")
        return 1
    print(f"ok {len(skills)} skills, {len(cases)} cases")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Eval estrutural e de roteamento do catálogo — TDD."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import eval_catalog as mod

EXECUTION = """\
---
name: debug-hypotheses
description: >
  Use when debugging a defect or test failure. Not observability.
---

# Debug

## Quando não usar

- Observability (como logar)

## Desculpas que não valem

| Desculpa | Realidade |
|----------|-----------|
| É o Redis | Hipótese sem teste de morte |

## Conferência

- [ ] Hipóteses no chat
"""

PONTE = """\
---
name: channel-evolution
description: >
  Use when the user mentions Evolution API. Canonical skill is whatsapp-channel.
---

# Evolution é adapter

**REQUIRED SUB-SKILL:** `whatsapp-channel`.

## Conferência

- [ ] Li a canônica
"""

OBS = """\
---
name: observability
description: >
  Use when adding logs, metrics, traces. Not debug-hypotheses.
---

# Observabilidade

## Quando não usar

- Debug por hipóteses

## Desculpas que não valem

| Desculpa | Realidade |
|----------|-----------|
| Logar o body | PII |

## Conferência

- [ ] Sem PII
"""


def _write_skill(root: Path, folder: str, body: str) -> Path:
    path = root / folder
    path.mkdir(parents=True)
    skill = path / "SKILL.md"
    skill.write_text(body, encoding="utf-8")
    return skill


class ParseFrontmatterTest(unittest.TestCase):
    def test_folded_description_joins_lines(self) -> None:
        meta, body = mod.parse_frontmatter(EXECUTION)
        self.assertEqual(meta["name"], "debug-hypotheses")
        self.assertIn("debugging a defect", meta["description"])
        self.assertIn("Not observability", meta["description"])
        self.assertTrue(body.startswith("# Debug"))

    def test_rejects_missing_frontmatter(self) -> None:
        with self.assertRaises(mod.CatalogEvalError):
            mod.parse_frontmatter("# sem yaml\n")


class DiscoverTest(unittest.TestCase):
    def test_name_must_match_folder_and_ponte_is_detected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_skill(root / "quality", "debug-hypotheses", EXECUTION)
            _write_skill(root / "backend", "channel-evolution", PONTE)
            skills = mod.discover_skills(root)
            by_name = {s.name: s for s in skills}
            self.assertFalse(by_name["debug-hypotheses"].is_ponte)
            self.assertTrue(by_name["channel-evolution"].is_ponte)

    def test_name_mismatch_is_structural_error(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_skill(
                root / "quality",
                "wrong-folder",
                EXECUTION,
            )
            skills = mod.discover_skills(root)
            errors = mod.structural_errors(skills)
            self.assertTrue(any("name" in e for e in errors))


class AnatomyTest(unittest.TestCase):
    def test_execution_requires_quando_nao_usar_and_desculpas(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            thin = """\
---
name: http-apis
description: Use when creating a REST API.
---

# APIs

## Conferência

- [ ] Schema
"""
            _write_skill(root / "backend", "http-apis", thin)
            skills = mod.discover_skills(root)
            errors = mod.structural_errors(skills)
            self.assertTrue(any("Quando não usar" in e for e in errors))
            self.assertTrue(any("Desculpas" in e for e in errors))

    def test_ponte_does_not_need_anatomy(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_skill(root / "backend", "channel-evolution", PONTE)
            skills = mod.discover_skills(root)
            self.assertEqual(mod.structural_errors(skills), [])


class RoutingTest(unittest.TestCase):
    def test_positive_prompt_ranks_owner_first(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_skill(root / "quality", "debug-hypotheses", EXECUTION)
            _write_skill(root / "backend", "observability", OBS)
            skills = mod.discover_skills(root)
            ranked = mod.rank_prompt(
                "this test failed and I need the root cause",
                skills,
            )
            self.assertEqual(ranked[0].name, "debug-hypotheses")

    def test_negative_prompt_owner_outranks_this_skill(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_skill(root / "quality", "debug-hypotheses", EXECUTION)
            _write_skill(root / "backend", "observability", OBS)
            skills = mod.discover_skills(root)
            ranked = mod.rank_prompt(
                "add structured logs and RED metrics without PII",
                skills,
            )
            self.assertEqual(ranked[0].name, "observability")


class CollisionTest(unittest.TestCase):
    def test_near_duplicate_descriptions_fail(self) -> None:
        twin = EXECUTION.replace("name: debug-hypotheses", "name: other-debug")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_skill(root / "quality", "debug-hypotheses", EXECUTION)
            _write_skill(root / "quality", "other-debug", twin)
            skills = mod.discover_skills(root)
            hits = mod.collisions(skills, fail_at=0.75)
            self.assertTrue(hits)


class CasesCoverageTest(unittest.TestCase):
    def test_cases_cover_every_execution_skill_in_this_repo(self) -> None:
        root = Path(__file__).resolve().parents[2]
        skills = [s for s in mod.discover_skills(root) if not s.is_ponte]
        cases = mod.load_cases(root)
        missing = sorted({s.name for s in skills} - set(cases))
        self.assertEqual(missing, [])
        for name, spec in cases.items():
            self.assertGreaterEqual(len(spec.positive), 3, name)
            self.assertGreaterEqual(len(spec.negative), 2, name)


class LiveCatalogRoutingTest(unittest.TestCase):
    def test_positive_prompts_rank_owner_first(self) -> None:
        root = Path(__file__).resolve().parents[2]
        skills = mod.discover_skills(root)
        cases = mod.load_cases(root)
        failures = mod.evaluate_triggers(skills, cases)
        self.assertEqual(failures, [])

    def test_execution_skills_have_anatomy(self) -> None:
        root = Path(__file__).resolve().parents[2]
        self.assertEqual(mod.structural_errors(mod.discover_skills(root)), [])


if __name__ == "__main__":
    unittest.main()

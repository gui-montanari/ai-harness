#!/usr/bin/env python3
"""complete-until-done e debug-hypotheses: erro visto na verificação impede pronto."""

from __future__ import annotations

import unittest
from pathlib import Path

RULES = Path(__file__).resolve().parent


def _fold(text: str) -> str:
    return text.casefold()


class VerificationErrorIsDefectTest(unittest.TestCase):
    def test_complete_until_done_rejects_observation_exemption(self) -> None:
        text = _fold((RULES / "complete-until-done.md").read_text(encoding="utf-8"))
        for needle in (
            "não é observação",
            "não é isenção",
            "debug-hypotheses",
            "gravação",
            "fallback",
        ):
            self.assertIn(_fold(needle), text)

    def test_debug_hypotheses_fires_on_verification_failure(self) -> None:
        text = _fold((RULES / "debug-hypotheses.md").read_text(encoding="utf-8"))
        self.assertIn(_fold("verificação"), text)
        self.assertIn(_fold("pronto"), text)

    def test_debug_skill_flags_observation_with_exception(self) -> None:
        skill = RULES.parent / "quality" / "debug-hypotheses" / "SKILL.md"
        text = skill.read_text(encoding="utf-8")
        self.assertIn("não bloqueia", text)
        self.assertIn("complete-until-done", text)


if __name__ == "__main__":
    unittest.main()

#!/usr/bin/env python3
"""commit-identity: só trailer Anthropic/Claude; arquivo chamado claude.md passa."""

from __future__ import annotations

import unittest

import commit_identity_guard as mod

CASES = {
    "coauthor": (
        'git commit -m "fix" --trailer "Co-Authored-By: Claude <noreply@anthropic.com>"',
        "deny",
    ),
    "message coauthor": (
        'git commit -m "Co-Authored-By: Claude <noreply@anthropic.com>"',
        "deny",
    ),
    "claude file": ("git commit -m 'docs' -- claude.md", "allow"),
    "normal": ("git commit -m 'corrige hook'", "allow"),
}


class CommitIdentityGuardTest(unittest.TestCase):
    def test_cases(self) -> None:
        for name, (command, want) in CASES.items():
            with self.subTest(name):
                got = mod.decide(
                    {
                        "toolName": "run_terminal_command",
                        "toolInput": {"command": command},
                    }
                )["decision"]
                self.assertEqual(got, want)


if __name__ == "__main__":
    unittest.main()

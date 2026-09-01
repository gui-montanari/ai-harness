#!/usr/bin/env python3
"""git-destructive-guard: argv, -C, -f; lease e commit comum passam."""

from __future__ import annotations

import unittest

import git_destructive_guard as mod

CASES = {
    "hard": ("git reset --hard", "deny"),
    "hard -C": ("git -C /tmp/app reset --hard HEAD", "deny"),
    "push f": ("git push -f origin main", "deny"),
    "push force": ("git push --force origin main", "deny"),
    "lease": ("git push --force-with-lease origin main", "allow"),
    "branch D": ("git branch -D topic", "deny"),
    "checkout all": ("git checkout -- .", "deny"),
    "restore all": ("git restore .", "deny"),
    "clean": ("git clean -fd", "deny"),
    "commit": ("git commit -m 'fix'", "allow"),
    "chain": ("git add . && git reset --hard", "deny"),
}


class GitDestructiveGuardTest(unittest.TestCase):
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

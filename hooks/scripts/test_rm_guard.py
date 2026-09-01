#!/usr/bin/env python3
"""rm-guard: só caminho crítico, inclusive -fr e sudo; tmp de projeto passa."""

from __future__ import annotations

import os
import unittest
from pathlib import Path
from unittest import mock

import rm_guard

HOME = Path("/home/tenda")
WS = Path("/home/tenda/projetos/app")

CASES = {
    "root": ("rm -rf /", "deny"),
    "fr root": ("rm -fr /", "deny"),
    "sudo etc": ("sudo rm -rf /etc", "deny"),
    "home": ("rm --recursive --force /home/tenda", "deny"),
    "workspace": ("rm -rf /home/tenda/projetos/app", "deny"),
    "dot at root": ("rm -rf .", "deny"),
    "tmp": ("rm -rf /home/tenda/projetos/app/tmp", "allow"),
    "node_modules": ("rm -rf node_modules", "allow"),
    "not recursive": ("rm -f /home/tenda/.bashrc", "allow"),
    "countdown": ("countdown -v /", "allow"),
}


def decide(command: str) -> dict:
    return rm_guard.decide(
        {
            "toolName": "run_terminal_command",
            "toolInput": {"command": command},
            "cwd": str(WS),
            "workspaceRoot": str(WS),
        },
        home=HOME,
        workspace=WS,
    )


class RmGuardTest(unittest.TestCase):
    def test_cases(self) -> None:
        for name, (command, want) in CASES.items():
            with self.subTest(name):
                self.assertEqual(decide(command)["decision"], want)

    def test_ask_on_grok(self) -> None:
        with mock.patch.dict(os.environ, {"GROK_HOOK_EVENT": "pre_tool_use"}):
            self.assertEqual(decide("rm -rf /")["decision"], "ask")


if __name__ == "__main__":
    unittest.main()

#!/usr/bin/env python3
"""docker-guard: compose down -v e volume rm; countdown e down simples passam."""

from __future__ import annotations

import unittest

import docker_guard

CASES = {
    "compose v": ("docker compose down -v", "deny"),
    "compose volumes": ("docker compose --progress plain down --volumes", "deny"),
    "legacy": ("docker-compose down --volumes", "deny"),
    "volume rm": ("docker volume rm foo", "deny"),
    "prune volumes": ("docker system prune --volumes", "deny"),
    "down": ("docker compose down", "allow"),
    "countdown": ("countdown -v /app", "allow"),
    "ps": ("docker ps -a", "allow"),
}


class DockerGuardTest(unittest.TestCase):
    def test_cases(self) -> None:
        for name, (command, want) in CASES.items():
            with self.subTest(name):
                got = docker_guard.decide(
                    {
                        "toolName": "run_terminal_command",
                        "toolInput": {"command": command},
                    }
                )["decision"]
                self.assertEqual(got, want)


if __name__ == "__main__":
    unittest.main()

#!/usr/bin/env python3
"""ssh-prod-guard: Bash local passa; SSH/MCP de produção destrutivo não."""

from __future__ import annotations

import unittest

import ssh_prod_guard as mod


def bash(command: str) -> dict:
    return {"toolName": "run_terminal_command", "toolInput": {"command": command}}


CASES: list[tuple[str, dict, str]] = [
    ("local rm", bash("rm -rf /tmp/foo"), "allow"),
    ("local drop", bash('psql -c "DROP TABLE t"'), "allow"),
    ("ssh prod rm", bash("ssh deploy@prod-1 'rm -rf /var/www'"), "deny"),
    ("ssh hostinger", bash("ssh root@hostinger 'systemctl stop nginx'"), "deny"),
    ("ssh dev ls", bash("ssh user@dev.example.com ls"), "allow"),
    (
        "mcp",
        {
            "toolName": "ssh-hostinger__execute_command",
            "toolInput": {"command": "rm -rf /app"},
        },
        "deny",
    ),
    (
        "mcp ls",
        {
            "toolName": "ssh-hostinger__execute_command",
            "toolInput": {"command": "ls /app"},
        },
        "allow",
    ),
]


class SshProdGuardTest(unittest.TestCase):
    def test_cases(self) -> None:
        for name, payload, want in CASES:
            with self.subTest(name):
                self.assertEqual(mod.decide(payload)["decision"], want)


if __name__ == "__main__":
    unittest.main()

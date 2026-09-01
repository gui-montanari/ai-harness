#!/usr/bin/env python3
"""Testes do hook protect_secrets (sem invocar git de verdade)."""

from __future__ import annotations

import unittest

import protect_secrets as mod


def decision(payload: dict) -> str:
    return mod.decide(payload)["decision"]


def bash(command: str) -> dict:
    return {"toolName": "run_terminal_command", "toolInput": {"command": command}}


def write(path: str) -> dict:
    return {"toolName": "write", "toolInput": {"file_path": path, "content": "x"}}


CASES: list[tuple[str, dict, str]] = [
    ("stage all", bash("git add -A"), "allow"),
    ("env real", bash("git add path/to/.env"), "deny"),
    ("env example", bash("git add .env.example"), "allow"),
    ("mixed", bash("git add .env secrets.example/twilio.env.example"), "deny"),
    ("example dir", bash("git add secrets.example/twilio.env.example"), "allow"),
    ("rsa", bash("git add id_rsa"), "deny"),
    ("pem", bash("git add foo.pem"), "deny"),
    ("source", bash("git add app.py"), "allow"),
    ("creds", bash("git add credentials.json"), "deny"),
    ("git -C env", bash("git -C /app add .env"), "deny"),
    ("write env", write("/app/.env"), "allow"),
    ("write rsa", write("/app/id_rsa"), "deny"),
    ("write pem", write("/app/tls.pem"), "deny"),
    ("write py", write("/app/app.py"), "allow"),
]


class ProtectSecretsTest(unittest.TestCase):
    def test_cases(self) -> None:
        for name, payload, want in CASES:
            with self.subTest(name):
                self.assertEqual(decision(payload), want)

    def test_antigravity_command_line(self) -> None:
        got = mod.decide({"toolCall": {"args": {"CommandLine": "git add .env"}}})
        self.assertEqual(got["decision"], "deny")


if __name__ == "__main__":
    unittest.main()

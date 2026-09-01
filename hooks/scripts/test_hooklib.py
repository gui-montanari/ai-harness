#!/usr/bin/env python3
"""Contrato do hooklib: payload, argv, git -C, ask vs deny."""

from __future__ import annotations

import os
import unittest
from pathlib import Path
from unittest import mock

import hooklib


class HooklibTest(unittest.TestCase):
    def test_command_from_grok_and_antigravity(self) -> None:
        grok = hooklib.command_text({"toolInput": {"command": "git reset --hard"}})
        agy = hooklib.command_text(
            {"toolCall": {"args": {"CommandLine": "git reset --hard"}}}
        )
        self.assertEqual(grok, agy)

    def test_splits_and_keeps_quoted_sql(self) -> None:
        parts = hooklib.chunks('psql -c "DELETE FROM t" && echo done')
        self.assertEqual(parts[0], 'psql -c "DELETE FROM t"')
        self.assertEqual(hooklib.argv(parts[0])[-1], "DELETE FROM t")

    def test_git_c_before_subcommand(self) -> None:
        calls = hooklib.git_calls(
            "git -C /tmp/app --no-pager reset --hard", cwd=Path("/home")
        )
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0].subcommand, "reset")
        self.assertTrue(calls[0].has("--hard"))
        self.assertEqual(calls[0].repo, Path("/tmp/app"))

    def test_git_and_chain(self) -> None:
        calls = hooklib.git_calls("git add . && git reset --hard")
        self.assertEqual([c.subcommand for c in calls], ["add", "reset"])

    def test_force_clustered_short_flag(self) -> None:
        call = hooklib.git_calls("git push -uf origin main")[0]
        self.assertTrue(call.has("-f", "--force"))
        self.assertFalse(call.has("--force-with-lease"))

    def test_confirm_asks_on_grok_denies_elsewhere(self) -> None:
        with mock.patch.dict(os.environ, {"GROK_HOOK_EVENT": "pre_tool_use"}):
            self.assertEqual(hooklib.confirm("x")["decision"], hooklib.ASK)
        with mock.patch.dict(os.environ, {}, clear=True):
            os.environ.pop("GROK_HOOK_EVENT", None)
            self.assertEqual(hooklib.confirm("x")["decision"], hooklib.DENY)


if __name__ == "__main__":
    unittest.main()

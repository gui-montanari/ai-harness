#!/usr/bin/env python3
"""Rules: um catálogo, um canal nativo por host, overlay fora do git público."""

from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path
from unittest import mock

MODULE_PATH = Path(__file__).resolve().parent / "sync.py"
SPEC = importlib.util.spec_from_file_location("harness_rules_sync", MODULE_PATH)
sync = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(sync)


class RulesSyncTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.home = Path(self.temp.name) / "home"
        self.home.mkdir()
        self.canon = Path(__file__).resolve().parents[1]
        self.overlay = self.home / ".config/ai-harness/overlay/rules"
        self.patches = [
            mock.patch.object(sync, "HOME", self.home),
            mock.patch.object(sync, "CANON", self.canon),
            mock.patch.object(sync, "OVERLAY", self.overlay),
            mock.patch.object(sync, "PUBLIC", self.canon / "rules"),
        ]
        for patch in self.patches:
            patch.start()

    def tearDown(self):
        for patch in reversed(self.patches):
            patch.stop()
        self.temp.cleanup()

    def test_catalog_is_the_global_gates_not_readme_or_example(self):
        items = sync.catalog()
        names = {item.name for item in items}
        self.assertEqual(
            names,
            {
                "analyze-before-implement",
                "ask-before-contract",
                "complete-until-done",
                "debug-hypotheses",
                "git-activity",
                "git-discipline",
            },
        )
        for item in items:
            self.assertTrue(item.path.is_file())
            self.assertFalse(item.overlay)

    def test_overlay_rule_is_merged_and_not_in_public_repo(self):
        self.overlay.mkdir(parents=True)
        path = self.overlay / "stockfy-repos-autorizacao.md"
        path.write_text("# Stockfy\n")
        items = sync.catalog()
        by_name = {item.name: item for item in items}
        self.assertIn("stockfy-repos-autorizacao", by_name)
        self.assertTrue(by_name["stockfy-repos-autorizacao"].overlay)
        self.assertFalse((self.canon / "rules" / "stockfy-repos-autorizacao.md").exists())

    def test_grok_and_cursor_get_native_symlinks(self):
        sync.sync()
        grok = self.home / ".grok" / "rules" / "git-discipline.md"
        cursor = self.home / ".cursor" / "rules" / "git-discipline.mdc"
        self.assertTrue(grok.is_symlink())
        self.assertTrue(cursor.is_symlink())
        self.assertEqual(grok.resolve(), (self.canon / "rules" / "git-discipline.md").resolve())
        self.assertEqual(cursor.resolve(), grok.resolve())

    def test_codex_agents_md_gets_rule_bodies_claude_md_does_not(self):
        claude_md = self.home / ".claude" / "CLAUDE.md"
        claude_md.parent.mkdir(parents=True)
        claude_md.write_text(
            "preamble\n<!-- gui-montanari-skills -->\nold\n<!-- /gui-montanari-skills -->\n"
        )
        sync.sync()
        codex = (self.home / ".codex" / "AGENTS.md").read_text()
        self.assertIn("<!-- ai-harness-rules -->", codex)
        self.assertIn("# Disciplina de git", codex)
        self.assertIn("# Completar até o fim", codex)
        claude = claude_md.read_text()
        self.assertNotIn("gui-montanari-skills", claude)
        self.assertNotIn("<!-- ai-harness-rules -->", claude)
        self.assertIn("preamble", claude)

    def test_stray_host_copy_moves_to_overlay_once(self):
        grok_dir = self.home / ".grok" / "rules"
        grok_dir.mkdir(parents=True)
        stray = grok_dir / "stockfy-repos-autorizacao.md"
        stray.write_text("# Stockfy\nlocal\n")
        sync.sync()
        overlay = self.overlay / "stockfy-repos-autorizacao.md"
        self.assertTrue(overlay.is_file())
        self.assertIn("local", overlay.read_text())
        self.assertTrue((grok_dir / "stockfy-repos-autorizacao.md").is_symlink())

    def test_grok_compat_is_native_only_and_preserves_the_rest_of_config(self):
        text = (
            '[models]\ndefault = "grok-4.6"\n\n'
            "# gui-montanari-skills: catalog rules live in ~/.grok/rules (mirrored to\n"
            "# Cursor/Claude). Keep vendor rule scan off so Grok does not load them 3x.\n"
            "[compat.cursor]\nrules = false\n\n[mcp_servers.x]\ncommand = \"npx\"\n"
        )
        out = sync.ensure_grok_compat(text)
        self.assertIn("default = \"grok-4.6\"", out)
        self.assertIn("[mcp_servers.x]", out)
        self.assertNotIn("gui-montanari-skills: catalog rules", out)
        self.assertIn("Grok só lê nativo", out)
        for section in ("cursor", "claude"):
            chunk = out.split(f"[compat.{section}]")[1].split("[")[0]
            for key in ("rules", "hooks", "agents", "skills", "mcps"):
                self.assertIn(f"{key} = false", chunk)


if __name__ == "__main__":
    unittest.main()

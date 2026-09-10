#!/usr/bin/env python3
"""Subagents: um catálogo, projeção nativa por host, overlay fora do git público."""

from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path
from unittest import mock

MODULE_PATH = Path(__file__).resolve().parent / "sync.py"
SPEC = importlib.util.spec_from_file_location("harness_subagents_sync", MODULE_PATH)
sync = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(sync)


class SubagentsSyncTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.home = Path(self.temp.name) / "home"
        self.home.mkdir()
        self.public = Path(self.temp.name) / "subagents"
        self.public.mkdir()
        self.overlay = self.home / ".config/ai-harness/overlay/subagents"
        self.legacy = self.home / ".config/ai-harness/overlay/agents"
        self.patches = [
            mock.patch.object(sync, "HOME", self.home),
            mock.patch.object(sync, "PUBLIC", self.public),
            mock.patch.object(sync, "OVERLAY", self.overlay),
            mock.patch.object(sync, "LEGACY_OVERLAY", self.legacy),
        ]
        for patch in self.patches:
            patch.start()

    def tearDown(self):
        for patch in reversed(self.patches):
            patch.stop()
        self.temp.cleanup()

    def test_catalog_ignores_readme_and_example(self):
        (self.public / "README.md").write_text("# Subagents\n")
        (self.public / "overlay.example.md").write_text("# Exemplo\n")
        (self.public / "reviewer.md").write_text("---\nname: reviewer\n---\n# Reviewer\n")
        names = {item.name for item in sync.catalog()}
        self.assertEqual(names, {"reviewer"})
        self.assertFalse(next(iter(sync.catalog())).overlay)

    def test_overlay_merges_and_is_not_public(self):
        self.overlay.mkdir(parents=True)
        (self.overlay / "oracle-prophet-ml.md").write_text(
            "---\nname: oracle-prophet-ml\n---\n# OracleProphet\n"
        )
        items = {item.name: item for item in sync.catalog()}
        self.assertIn("oracle-prophet-ml", items)
        self.assertTrue(items["oracle-prophet-ml"].overlay)
        self.assertFalse((self.public / "oracle-prophet-ml.md").exists())

    def test_legacy_overlay_agents_moves_to_subagents(self):
        self.legacy.mkdir(parents=True)
        (self.legacy / "oracle-prophet-ml.md").write_text(
            "---\nname: oracle-prophet-ml\n---\n# OracleProphet\n"
        )
        items = {item.name: item for item in sync.catalog()}
        self.assertTrue(items["oracle-prophet-ml"].overlay)
        self.assertEqual(items["oracle-prophet-ml"].path, self.overlay / "oracle-prophet-ml.md")
        self.assertFalse(self.legacy.exists())

    def test_legacy_overlay_drops_names_that_became_public(self):
        (self.public / "python-fastapi-architect.md").write_text(
            "---\nname: python-fastapi-architect\n---\n# Público\n"
        )
        self.legacy.mkdir(parents=True)
        (self.legacy / "python-fastapi-architect.md").write_text(
            "---\nname: python-fastapi-architect\n---\n# Overlay velho\n"
        )
        items = {item.name: item for item in sync.catalog()}
        self.assertFalse(items["python-fastapi-architect"].overlay)
        self.assertIn("Público", items["python-fastapi-architect"].path.read_text())
        self.assertFalse((self.overlay / "python-fastapi-architect.md").exists())

    def test_cursor_and_claude_get_symlinks(self):
        (self.public / "reviewer.md").write_text("---\nname: reviewer\n---\n# Reviewer\n")
        sync.sync()
        cursor = self.home / ".cursor" / "agents" / "reviewer.md"
        claude = self.home / ".claude" / "agents" / "reviewer.md"
        self.assertTrue(cursor.is_symlink())
        self.assertTrue(claude.is_symlink())
        self.assertEqual(cursor.resolve(), (self.public / "reviewer.md").resolve())
        self.assertEqual(claude.resolve(), cursor.resolve())

    def test_stray_host_copy_moves_to_overlay_once(self):
        claude_dir = self.home / ".claude" / "agents"
        claude_dir.mkdir(parents=True)
        stray = claude_dir / "oracle-prophet-ml.md"
        stray.write_text("---\nname: oracle-prophet-ml\n---\n# OracleProphet\n")
        sync.sync()
        overlay = self.overlay / "oracle-prophet-ml.md"
        self.assertTrue(overlay.is_file())
        self.assertIn("OracleProphet", overlay.read_text())
        linked = claude_dir / "oracle-prophet-ml.md"
        self.assertTrue(linked.is_symlink())
        self.assertEqual(linked.resolve(), overlay.resolve())
        cursor = self.home / ".cursor" / "agents" / "oracle-prophet-ml.md"
        self.assertTrue(cursor.is_symlink())
        self.assertEqual(cursor.resolve(), overlay.resolve())

    def test_public_fastapi_roles_are_not_product_overlay(self):
        for name in sync.PUBLIC_FASTAPI:
            (self.public / f"{name}.md").write_text(f"---\nname: {name}\n---\n# FastAPI\n")
        names = {item.name for item in sync.catalog()}
        self.assertTrue(set(sync.PUBLIC_FASTAPI).issubset(names))
        self.assertNotIn("oracle-prophet-ml", names)


class PublicCatalogContractTest(unittest.TestCase):
    def test_fastapi_roles_live_in_harness_git(self):
        root = Path(__file__).resolve().parent
        for name in sync.PUBLIC_FASTAPI:
            path = root / f"{name}.md"
            self.assertTrue(path.is_file(), name)
            text = path.read_text()
            self.assertNotIn("vps-hermes-one", text)
            self.assertNotIn("OracleProphet", text)

    def test_oracle_prophet_is_not_public(self):
        path = Path(__file__).resolve().parent / "oracle-prophet-ml.md"
        self.assertFalse(path.exists())


if __name__ == "__main__":
    unittest.main()

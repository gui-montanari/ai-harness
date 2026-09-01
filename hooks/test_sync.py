#!/usr/bin/env python3
"""O catálogo de hooks chega igual em cada host, sem apagar config alheia."""

from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

MODULE_PATH = Path(__file__).resolve().parent / "sync.py"
SPEC = importlib.util.spec_from_file_location("harness_hooks_sync", MODULE_PATH)
sync = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(sync)


class HookSyncTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.home = Path(self.temp.name) / "home"
        self.home.mkdir()
        self.canon = Path(__file__).resolve().parents[1]
        self.overlay = self.home / ".config/ai-harness/overlay/hooks"
        self.patches = [
            mock.patch.object(sync, "HOME", self.home),
            mock.patch.object(sync, "CANON", self.canon),
            mock.patch.object(sync, "OVERLAY", self.overlay),
        ]
        for patch in self.patches:
            patch.start()

    def tearDown(self):
        for patch in reversed(self.patches):
            patch.stop()
        self.temp.cleanup()

    def test_catalog_has_unique_hooks_and_scripts(self):
        items = sync.catalog()
        self.assertIn("protect-secrets", items)
        self.assertIn("rm-guard", items)
        for name, spec in items.items():
            path = sync.script_path(spec)
            self.assertTrue(path.exists(), name)

    def test_grok_replaces_dangling_symlink(self):
        dest = self.home / ".grok" / "hooks"
        dest.mkdir(parents=True)
        broken = dest / "protect-secrets.json"
        broken.symlink_to("/tmp/does-not-exist-harness-hook.json")
        sync.sync_grok(sync.catalog())
        self.assertTrue(broken.is_file())
        self.assertFalse(broken.is_symlink())

    def test_grok_writes_one_json_per_hook(self):
        items = sync.catalog()
        sync.sync_grok(items)
        dest = self.home / ".grok" / "hooks"
        self.assertTrue((dest / "protect-secrets.json").exists())
        self.assertTrue((dest / "rm-guard.json").exists())
        data = json.loads((dest / "protect-secrets.json").read_text())
        command = data["hooks"]["PreToolUse"][0]["hooks"][0]["command"]
        self.assertIn("protect_secrets.py", command)

    def test_grok_command_is_unquoted_so_the_runner_does_not_prefix_hooks_dir(self):
        items = sync.catalog()
        sync.sync_grok(items)
        dest = self.home / ".grok" / "hooks"
        python_cmd = json.loads((dest / "protect-secrets.json").read_text())["hooks"]["PreToolUse"][0]["hooks"][0]["command"]
        rm_cmd = json.loads((dest / "rm-guard.json").read_text())["hooks"]["PreToolUse"][0]["hooks"][0]["command"]
        self.assertTrue(python_cmd.startswith("/"), python_cmd)
        self.assertNotIn('"', python_cmd)
        self.assertTrue(python_cmd.endswith("protect_secrets.py"), python_cmd)
        self.assertTrue(rm_cmd.startswith("/"), rm_cmd)
        self.assertNotIn('"', rm_cmd)
        self.assertTrue(rm_cmd.endswith("rm_guard.py"))

    def test_cursor_keeps_unrelated_hooks(self):
        dest = self.home / ".cursor" / "hooks.json"
        dest.parent.mkdir(parents=True)
        dest.write_text(
            json.dumps(
                {
                    "version": 1,
                    "hooks": {
                        "beforeShellExecution": [
                            {"command": "echo custom", "matcher": "foo"}
                        ]
                    },
                }
            )
        )
        sync.sync_cursor(sync.catalog())
        data = json.loads(dest.read_text())
        commands = [item["command"] for item in data["hooks"]["beforeShellExecution"]]
        self.assertIn("echo custom", commands)
        self.assertTrue(any("protect_secrets.py" in cmd for cmd in commands))

    def test_claude_preserves_permissions(self):
        dest = self.home / ".claude" / "settings.json"
        dest.parent.mkdir(parents=True)
        dest.write_text(json.dumps({"permissions": {"allow": ["Bash(ls)"]}, "hooks": {}}))
        sync.sync_claude(sync.catalog())
        data = json.loads(dest.read_text())
        self.assertEqual(data["permissions"]["allow"], ["Bash(ls)"])
        self.assertTrue(data["hooks"]["PreToolUse"])

    def test_overlay_hook_is_merged(self):
        scripts = self.overlay / "scripts"
        scripts.mkdir(parents=True)
        (scripts / "extra.sh").write_text("#!/bin/bash\nexit 0\n")
        (self.overlay / "catalog.json").write_text(
            json.dumps(
                {
                    "hooks": {
                        "extra-guard": {
                            "script": "extra.sh",
                            "runtime": "bash",
                            "timeout": 5,
                            "events": {"PreToolUse": {"matcher": "Bash"}},
                        }
                    }
                }
            )
        )
        items = sync.catalog()
        self.assertIn("extra-guard", items)
        sync.sync_grok(items)
        self.assertTrue((self.home / ".grok/hooks/extra-guard.json").exists())

    def test_antigravity_uses_named_hooks(self):
        sync.sync_antigravity(sync.catalog())
        data = json.loads((self.home / ".gemini/config/hooks.json").read_text())
        self.assertIn("protect-secrets", data)
        self.assertEqual(data["protect-secrets"]["PreToolUse"][0]["matcher"], "run_command")


if __name__ == "__main__":
    unittest.main()

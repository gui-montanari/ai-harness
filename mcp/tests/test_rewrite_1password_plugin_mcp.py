import importlib.util
import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "rewrite_1password_plugin_mcp.py"
SPEC = importlib.util.spec_from_file_location("rewrite_1password_plugin_mcp", MODULE_PATH)
rewrite = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(rewrite)

WRAPPER = Path(__file__).resolve().parents[1] / "scripts" / "run-1password-mcp"


class Rewrite1PasswordPluginMcpTest(unittest.TestCase):
    def test_replaces_bare_command_with_absolute_wrapper(self):
        with tempfile.TemporaryDirectory() as tmp:
            wrapper = Path(tmp) / "run-1password-mcp"
            plugin = Path(tmp) / "mcp.json"
            plugin.write_text(json.dumps({
                "mcpServers": {"1password": {"command": "1password-mcp", "args": []}}
            }))
            self.assertTrue(rewrite.rewrite_1password_plugin_mcp(plugin, wrapper))
            data = json.loads(plugin.read_text())
            self.assertEqual(
                data["mcpServers"]["1password"],
                {"command": "bash", "args": [str(wrapper)], "env": {}},
            )

    def test_is_idempotent(self):
        with tempfile.TemporaryDirectory() as tmp:
            wrapper = Path(tmp) / "run-1password-mcp"
            plugin = Path(tmp) / "mcp.json"
            plugin.write_text(json.dumps({
                "mcpServers": {
                    "1password": {"command": "bash", "args": [str(wrapper)], "env": {}}
                }
            }))
            self.assertFalse(rewrite.rewrite_1password_plugin_mcp(plugin, wrapper))


class Run1PasswordMcpTest(unittest.TestCase):
    def test_script_is_executable(self):
        self.assertTrue(os.access(WRAPPER, os.X_OK))

    def test_fails_closed_when_binary_missing(self):
        env = os.environ.copy()
        env["HOME"] = tempfile.mkdtemp()
        env["PATH"] = "/usr/bin:/bin"
        result = subprocess.run(
            [str(WRAPPER)],
            capture_output=True,
            text=True,
            timeout=5,
            env=env,
        )
        self.assertEqual(result.returncode, 127)
        self.assertIn("ausente", result.stderr)


if __name__ == "__main__":
    unittest.main()

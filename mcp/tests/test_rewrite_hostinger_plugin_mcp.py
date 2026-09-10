import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "rewrite_hostinger_plugin_mcp.py"
SPEC = importlib.util.spec_from_file_location("rewrite_hostinger_plugin_mcp", MODULE_PATH)
rewrite = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(rewrite)


class RewriteHostingerPluginMcpTest(unittest.TestCase):
    def test_replaces_npx_latest_with_local_node_wrapper(self):
        with tempfile.TemporaryDirectory() as tmp:
            wrapper = Path(tmp) / "run-hostinger-plugin"
            wrapper.write_text("#!/bin/bash\n")
            plugin = Path(tmp) / "mcp.json"
            plugin.write_text(json.dumps({
                "mcpServers": {
                    "hostinger-wordpress": {
                        "command": "npx",
                        "args": ["--yes", "--package=hostinger-api-mcp@latest", "hostinger-wordpress-mcp"],
                        "env": {"USER_AGENT": "plugin;cursor;0.2.0"},
                    }
                }
            }))
            self.assertTrue(rewrite.rewrite_hostinger_plugin_mcp(plugin, wrapper))
            data = json.loads(plugin.read_text())
            self.assertEqual(
                data["mcpServers"]["hostinger-wordpress"],
                {
                    "command": "bash",
                    "args": [str(wrapper), "wordpress"],
                    "env": {"USER_AGENT": "plugin;cursor;0.2.0"},
                },
            )

    def test_is_idempotent(self):
        with tempfile.TemporaryDirectory() as tmp:
            wrapper = Path(tmp) / "run-hostinger-plugin"
            plugin = Path(tmp) / "mcp.json"
            plugin.write_text(json.dumps({
                "mcpServers": {
                    "hostinger-vps": {
                        "command": "bash",
                        "args": [str(wrapper), "vps"],
                        "env": {},
                    }
                }
            }))
            self.assertFalse(rewrite.rewrite_hostinger_plugin_mcp(plugin, wrapper))


if __name__ == "__main__":
    unittest.main()

import importlib.util
import json
import tempfile
import tomllib
import unittest
from pathlib import Path
from unittest import mock


MODULE_PATH = Path(__file__).resolve().parents[1] / "mcp_toolkit.py"
SPEC = importlib.util.spec_from_file_location("mcp_toolkit", MODULE_PATH)
toolkit = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(toolkit)


class RemoteServerSyncTest(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        self.home = self.root / "home"
        self.home.mkdir()
        self.catalog_path = self.root / "mcp-catalog.json"
        self.catalog_path.write_text(json.dumps({
            "servers": {
                "cloudflare-api": {"url": "https://mcp.cloudflare.com/mcp"},
                "local-test": {"command": "printf", "args": ["ready"]},
            }
        }))
        self.patches = [
            mock.patch.object(toolkit, "HOME", self.home),
            mock.patch.object(toolkit, "CONFIG", self.home / ".config/ai-harness"),
            mock.patch.object(toolkit, "CATALOG_PATH", self.catalog_path),
            mock.patch.object(toolkit, "STATE_DIR", self.home / ".config/ai-harness/selections"),
            mock.patch.object(toolkit, "SECRETS_DIR", self.home / ".config/ai-harness/secrets"),
            mock.patch.object(toolkit, "MANAGED_STATE", self.home / ".config/ai-harness/managed-names.json"),
            mock.patch.object(toolkit, "OVERLAY", self.home / ".config/ai-harness/overlay/mcp"),
        ]
        for patch in self.patches:
            patch.start()

    def tearDown(self):
        for patch in reversed(self.patches):
            patch.stop()
        self.temp_dir.cleanup()

    def test_remote_server_is_rendered_for_every_client(self):
        enabled = {"cloudflare-api"}

        toolkit.sync_claude(enabled)
        toolkit.sync_codex(enabled)
        with mock.patch.object(toolkit, "opencode_path", return_value=self.home / ".config/opencode/opencode.json"):
            toolkit.sync_opencode(enabled)
        toolkit.sync_agy(enabled)
        toolkit.sync_grok(enabled)
        toolkit.sync_cursor(enabled)

        claude = json.loads((self.home / ".claude.json").read_text())
        self.assertEqual(
            claude["mcpServers"]["cloudflare-api"],
            {"type": "http", "url": "https://mcp.cloudflare.com/mcp"},
        )

        codex = tomllib.loads((self.home / ".codex-cli/config.toml").read_text())
        self.assertEqual(codex["mcp_servers"]["cloudflare-api"]["url"], "https://mcp.cloudflare.com/mcp")

        opencode = json.loads((self.home / ".config/opencode/opencode.json").read_text())
        self.assertEqual(
            opencode["mcp"]["cloudflare-api"],
            {"type": "remote", "url": "https://mcp.cloudflare.com/mcp", "enabled": True},
        )

        agy = json.loads((self.home / ".gemini/config/mcp_config.json").read_text())
        self.assertEqual(
            agy["mcpServers"]["cloudflare-api"],
            {
                "$typeName": toolkit.AGY_REMOTE_TYPE,
                "serverUrl": "https://mcp.cloudflare.com/mcp",
                "disabled": False,
            },
        )

        grok = tomllib.loads((self.home / ".grok/config.toml").read_text())
        self.assertEqual(
            grok["mcp_servers"]["cloudflare-api"],
            {"url": "https://mcp.cloudflare.com/mcp", "enabled": True},
        )

        cursor = json.loads((self.home / ".cursor/mcp.json").read_text())
        self.assertEqual(
            cursor["mcpServers"]["cloudflare-api"],
            {"url": "https://mcp.cloudflare.com/mcp"},
        )

    def test_disabled_remote_server_stays_available_in_clients_that_support_disabled_entries(self):
        toolkit.sync_claude(set())
        with mock.patch.object(toolkit, "opencode_path", return_value=self.home / ".config/opencode/opencode.json"):
            toolkit.sync_opencode(set())
        toolkit.sync_agy(set())
        toolkit.sync_grok(set())
        toolkit.sync_cursor(set())

        claude = json.loads((self.home / ".claude.json").read_text())
        self.assertIn("cloudflare-api", claude["mcpServersDisabled"])

        opencode = json.loads((self.home / ".config/opencode/opencode.json").read_text())
        self.assertFalse(opencode["mcp"]["cloudflare-api"]["enabled"])

        agy = json.loads((self.home / ".gemini/config/mcp_config.json").read_text())
        self.assertTrue(agy["mcpServers"]["cloudflare-api"]["disabled"])

        grok = tomllib.loads((self.home / ".grok/config.toml").read_text())
        self.assertFalse(grok["mcp_servers"]["cloudflare-api"]["enabled"])

        cursor = json.loads((self.home / ".cursor/mcp.json").read_text())
        self.assertNotIn("cloudflare-api", cursor.get("mcpServers", {}))

    def test_empty_agy_config_is_initialized(self):
        path = self.home / ".gemini/config/mcp_config.json"
        path.parent.mkdir(parents=True)
        path.write_text("")

        toolkit.sync_agy({"local-test"})

        data = json.loads(path.read_text())
        self.assertFalse(data["mcpServers"]["local-test"]["disabled"])

    def test_grok_sync_preserves_unrelated_config_and_replaces_managed_server(self):
        path = self.home / ".grok/config.toml"
        path.parent.mkdir(parents=True)
        path.write_text(
            '[ui]\ncompact_mode = true\n\n'
            '[mcp_servers.local-test]\ncommand = "old"\nenabled = false\n\n'
            '[mcp_servers.custom]\ncommand = "custom"\n'
        )

        toolkit.sync_grok({"local-test"})
        first_sync = path.read_text()
        toolkit.sync_grok({"local-test"})

        data = tomllib.loads(path.read_text())
        self.assertTrue(data["ui"]["compact_mode"])
        self.assertEqual(data["mcp_servers"]["custom"]["command"], "custom")
        self.assertEqual(data["mcp_servers"]["local-test"]["command"], "printf")
        self.assertTrue(data["mcp_servers"]["local-test"]["enabled"])
        self.assertEqual(path.read_text(), first_sync)

    def test_menu_keeps_stable_numbers_and_splits_active_from_inactive(self):
        names = ["alpha", "beta", "gamma"]
        first = toolkit.format_menu("grok", names, {"beta"})
        toggled = toolkit.format_menu("grok", names, {"alpha", "beta"})
        self.assertEqual(first[0], "MCPs para grok:")
        self.assertIn("Ativos:", first)
        self.assertIn("Inativos:", first)
        self.assertIn("  2. beta", first)
        self.assertIn("  1. alpha", first)
        self.assertIn("  3. gamma", first)
        ativos = first.index("Ativos:")
        inativos = first.index("Inativos:")
        self.assertLess(ativos, first.index("  2. beta"))
        self.assertGreater(first.index("  2. beta"), ativos)
        self.assertLess(first.index("  2. beta"), inativos)
        self.assertGreater(first.index("  1. alpha"), inativos)
        self.assertIn("  2. beta", toggled)
        self.assertLess(toggled.index("  1. alpha"), toggled.index("Inativos:"))
        self.assertGreater(toggled.index("  3. gamma"), toggled.index("Inativos:"))

    def test_menu_colors_active_green_and_inactive_red(self):
        lines = toolkit.format_menu("grok", ["alpha", "beta"], {"alpha"}, color=True)
        joined = "\n".join(lines)
        self.assertIn("\033[32m", joined)
        self.assertIn("\033[31m", joined)
        active = next(line for line in lines if "alpha" in line)
        inactive = next(line for line in lines if "beta" in line)
        self.assertTrue(active.startswith("\033[32m"), active)
        self.assertTrue(inactive.startswith("\033[31m"), inactive)
        plain = toolkit.format_menu("grok", ["alpha"], {"alpha"}, color=False)
        self.assertFalse(any("\033[" in line for line in plain))

    def test_overlay_catalog_is_merged(self):
        overlay = self.home / ".config/ai-harness/overlay/mcp"
        overlay.mkdir(parents=True)
        (overlay / "catalog.json").write_text(json.dumps({
            "servers": {"extra-local": {"command": "printf", "args": ["overlay"]}}
        }))
        self.assertIn("extra-local", toolkit.catalog())
        self.assertEqual(toolkit.catalog()["extra-local"]["command"], "printf")

    def test_grok_oauth_proxy_keeps_auth_timeout_long_enough_to_persist_tokens(self):
        self.catalog_path.write_text(json.dumps({
            "servers": {
                "cloudflare-api": {
                    "command": "npx",
                    "args": ["-y", "mcp-remote@0.1.38", "https://mcp.cloudflare.com/mcp"],
                }
            }
        }))
        toolkit.sync_grok({"cloudflare-api"})
        grok = tomllib.loads((self.home / ".grok/config.toml").read_text())
        server = grok["mcp_servers"]["cloudflare-api"]
        self.assertEqual(server["startup_timeout_sec"], 300)
        self.assertIn("--auth-timeout", server["args"])
        timeout_at = server["args"].index("--auth-timeout")
        self.assertEqual(server["args"][timeout_at + 1], "300")

    def test_mcp_remote_bearer_header_is_not_treated_as_browser_oauth(self):
        self.catalog_path.write_text(json.dumps({
            "servers": {
                "mercado-pago-oficial": {
                    "command": "npx",
                    "args": [
                        "-y",
                        "mcp-remote@0.1.38",
                        "https://mcp.mercadopago.com/mcp",
                        "--header",
                        "Authorization:Bearer ${TOKEN}",
                    ],
                }
            }
        }))
        toolkit.sync_grok({"mercado-pago-oficial"})
        grok = tomllib.loads((self.home / ".grok/config.toml").read_text())
        server = grok["mcp_servers"]["mercado-pago-oficial"]
        self.assertNotIn("startup_timeout_sec", server)
        self.assertNotIn("--auth-timeout", server["args"])

    def test_secret_backed_proxy_keeps_credentials_out_of_generated_config(self):
        self.catalog_path.write_text(json.dumps({
            "servers": {
                "mercado-pago-oficial": {
                    "command": "npx",
                    "args": [
                        "-y",
                        "mcp-remote@0.1.38",
                        "https://mcp.mercadopago.com/mcp",
                        "--header",
                        "Authorization:Bearer ${MERCADO_PAGO_ACCESS_TOKEN}",
                    ],
                    "secretFile": "mercado-pago.env",
                }
            }
        }))

        toolkit.sync_codex({"mercado-pago-oficial"})
        toolkit.sync_cursor({"mercado-pago-oficial"})

        generated = (self.home / ".codex-cli/config.toml").read_text()
        codex = tomllib.loads(generated)
        server = codex["mcp_servers"]["mercado-pago-oficial"]
        self.assertEqual(server["command"], "bash")
        self.assertTrue(any(arg.endswith("/mercado-pago.env") for arg in server["args"]))
        self.assertIn("Authorization:Bearer ${MERCADO_PAGO_ACCESS_TOKEN}", server["args"])
        self.assertNotIn("APP_USR-", generated)

        cursor_path = self.home / ".cursor/mcp.json"
        cursor_text = cursor_path.read_text()
        cursor = json.loads(cursor_text)
        cursor_server = cursor["mcpServers"]["mercado-pago-oficial"]
        self.assertEqual(cursor_server["command"], "bash")
        self.assertTrue(any(arg.endswith("/mercado-pago.env") for arg in cursor_server["args"]))
        self.assertIn("Authorization:Bearer ${MERCADO_PAGO_ACCESS_TOKEN}", cursor_server["args"])
        self.assertNotIn("APP_USR-", cursor_text)

    def test_cursor_sync_preserves_unrelated_servers_and_replaces_managed(self):
        path = self.home / ".cursor/mcp.json"
        path.parent.mkdir(parents=True)
        path.write_text(json.dumps({
            "mcpServers": {
                "custom": {"command": "echo", "args": ["keep"]},
                "local-test": {"command": "old"},
            }
        }))

        toolkit.sync_cursor({"local-test"})
        first_sync = path.read_text()
        toolkit.sync_cursor({"local-test"})

        data = json.loads(path.read_text())
        self.assertEqual(data["mcpServers"]["custom"], {"command": "echo", "args": ["keep"]})
        self.assertEqual(data["mcpServers"]["local-test"]["command"], "printf")
        self.assertEqual(data["mcpServers"]["local-test"]["args"], ["ready"])
        self.assertEqual(path.read_text(), first_sync)

    def test_empty_cursor_config_is_initialized(self):
        path = self.home / ".cursor/mcp.json"
        path.parent.mkdir(parents=True)
        path.write_text("")

        toolkit.sync_cursor({"local-test"})

        data = json.loads(path.read_text())
        self.assertEqual(data["mcpServers"]["local-test"]["command"], "printf")
        self.assertEqual(data["mcpServers"]["local-test"]["args"], ["ready"])


if __name__ == "__main__":
    unittest.main()

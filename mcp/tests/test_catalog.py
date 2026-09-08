import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class CatalogContractTest(unittest.TestCase):
    def setUp(self):
        self.catalog = json.loads((ROOT / "catalog/mcp-catalog.json").read_text())

    def test_catalog_has_unique_named_servers(self):
        servers = self.catalog["servers"]
        self.assertEqual(len(servers), len(set(servers)))
        self.assertTrue(servers)

    def test_every_server_has_exactly_one_transport(self):
        for name, config in self.catalog["servers"].items():
            with self.subTest(name=name):
                has_command = "command" in config
                has_url = "url" in config
                self.assertNotEqual(has_command, has_url)
                if has_command:
                    self.assertIsInstance(config["command"], str)
                    self.assertIsInstance(config.get("args", []), list)
                else:
                    self.assertRegex(config["url"], r"^https://")

    def test_secret_files_have_examples(self):
        for name, config in self.catalog["servers"].items():
            secret = config.get("secretFile")
            if secret:
                self.assertTrue((ROOT / "secrets.example" / f"{secret}.example").exists(), name)

    def test_repository_contains_no_known_secret_shapes(self):
        fragments = ["sk" + "-lf-", "pk" + "-lf-", "AT" + "ATT", "Br" + "Azur", "lrh" + "pk0", "6nY" + "jAr"]
        pattern = re.compile("(" + "|".join(fragments) + ")")
        for path in ROOT.rglob("*"):
            if path.is_file() and ".git" not in path.parts and "node_modules" not in path.parts:
                try:
                    text = path.read_text()
                except UnicodeDecodeError:
                    continue
                self.assertIsNone(pattern.search(text), str(path))

    def test_cloudflare_uses_native_http_oauth(self):
        cloudflare = self.catalog["servers"]["cloudflare-api"]
        self.assertEqual(cloudflare["url"], "https://mcp.cloudflare.com/mcp")
        self.assertNotIn("command", cloudflare)
        scopes = cloudflare["oauth"]["scopes"]
        self.assertEqual(scopes, ["user:read", "offline_access", "account:read"])
        self.assertNotIn("openid", scopes)
        self.assertNotIn("oauthTimeoutSec", cloudflare)

    def test_stripe_uses_native_http_oauth(self):
        stripe = self.catalog["servers"]["stripe"]
        self.assertEqual(stripe, {"url": "https://mcp.stripe.com"})
        self.assertNotIn("oauthTimeoutSec", stripe)

    def test_make_uses_the_official_oauth_endpoint(self):
        make = self.catalog["servers"]["make"]
        self.assertEqual(make["url"], "https://mcp.make.com")
        self.assertNotIn("command", make)
        scopes = make["oauth"]["scopes"]
        self.assertIn("mcp:use", scopes)
        self.assertNotIn("oauthTimeoutSec", make)

    def test_mcp_remote_browser_oauth_timeout_is_inferred_not_copied_per_server(self):
        for name, cfg in self.catalog["servers"].items():
            args = [str(a) for a in (cfg.get("args") or [])]
            if not any("mcp-remote" in a for a in args):
                continue
            with self.subTest(name=name):
                self.assertNotIn("oauthTimeoutSec", cfg)
                self.assertNotIn("--auth-timeout", args)

    def test_twilio_docs_uses_the_official_hosted_endpoint(self):
        self.assertEqual(
            self.catalog["servers"]["twilio-docs"],
            {"url": "https://mcp.twilio.com/docs"},
        )

    def test_public_catalog_has_no_machine_or_client_facts(self):
        text = (ROOT / "catalog/mcp-catalog.json").read_text().lower()
        for needle in ("stockfy", "187.127", "179.198", "autodin", "usedata", "projeto-sfy"):
            self.assertNotIn(needle, text)

    def test_twilio_api_uses_secret_backed_official_wrapper(self):
        self.assertEqual(
            self.catalog["servers"]["twilio"],
            {
                "command": "bash",
                "args": ["{toolkit}/mcp_servers/twilio/start.sh"],
                "secretFile": "twilio.env",
            },
        )


if __name__ == "__main__":
    unittest.main()

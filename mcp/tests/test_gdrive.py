import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
START = ROOT / "mcp_servers/gdrive/start.sh"


class GdriveStartTest(unittest.TestCase):
    def test_start_installs_sdk_when_node_modules_missing(self):
        text = START.read_text()
        self.assertIn("node_modules/@modelcontextprotocol/sdk", text)
        self.assertIn("npm ci", text)

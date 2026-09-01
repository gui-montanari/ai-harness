import os
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
START = ROOT / "mcp_servers/twilio/start.sh"


class TwilioWrapperTest(unittest.TestCase):
    def test_start_script_is_executable(self):
        self.assertTrue(START.is_file())
        self.assertTrue(os.access(START, os.X_OK))

    def test_start_script_fails_closed_without_secrets(self):
        env = {
            key: value
            for key, value in os.environ.items()
            if not key.startswith("TWILIO_")
        }
        result = subprocess.run(
            [str(START)],
            env=env,
            capture_output=True,
            text=True,
            timeout=5,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("TWILIO_ACCOUNT_SID", result.stderr)

    def test_wrapper_does_not_embed_credentials(self):
        text = START.read_text()
        self.assertNotRegex(text, r"AC[a-fA-F0-9]{32}")
        self.assertNotRegex(text, r"SK[a-fA-F0-9]{32}")
        self.assertIn(
            '"${TWILIO_ACCOUNT_SID}/${TWILIO_API_KEY}:${TWILIO_API_SECRET}"',
            text,
        )

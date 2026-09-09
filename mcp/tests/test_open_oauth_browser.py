#!/usr/bin/env python3
"""open-oauth-browser: Chrome com o perfil do overlay, senão o binário do sistema."""

from __future__ import annotations

import os
import stat
import subprocess
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "open-oauth-browser"


class OpenOauthBrowserTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.home = Path(self.temp.name)
        self.chrome = self.home / "fake-chrome"
        self.chrome.write_text("#!/bin/sh\nprintf '%s\\n' \"$@\"\n")
        self.chrome.chmod(self.chrome.stat().st_mode | stat.S_IEXEC)

    def tearDown(self):
        self.temp.cleanup()

    def _run(self, *url_args: str, conf: str | None) -> subprocess.CompletedProcess[str]:
        env = os.environ.copy()
        env["HOME"] = str(self.home)
        env["CHROME_BIN"] = str(self.chrome)
        if conf is not None:
            path = self.home / ".config/ai-harness/overlay/mcp/browser.env"
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(conf)
        return subprocess.run(
            [str(SCRIPT), *url_args],
            check=False,
            capture_output=True,
            text=True,
            env=env,
        )

    def test_overlay_profile_opens_new_window_in_that_directory(self):
        result = self._run("https://mcp.cloudflare.com/authorize", conf="CHROME_PROFILE_DIRECTORY=Default\n")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(
            result.stdout.splitlines(),
            [
                "--profile-directory=Default",
                "--new-window",
                "https://mcp.cloudflare.com/authorize",
            ],
        )

    def test_without_overlay_does_not_force_a_profile(self):
        result = self._run("https://mcp.make.com", conf=None)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), "https://mcp.make.com")


if __name__ == "__main__":
    unittest.main()

import os
import subprocess
import unittest
from pathlib import Path

START = Path(__file__).resolve().parents[1] / "scripts" / "run-hostinger-plugin"


class RunHostingerPluginTest(unittest.TestCase):
    def test_rejects_unknown_group(self):
        result = subprocess.run(
            [str(START), "not-a-group"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("inválido", result.stderr)

    def test_script_is_executable(self):
        self.assertTrue(os.access(START, os.X_OK))


if __name__ == "__main__":
    unittest.main()

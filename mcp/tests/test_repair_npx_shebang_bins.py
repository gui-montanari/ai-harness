import importlib.util
import tempfile
import unittest
from pathlib import Path

MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "repair_npx_shebang_bins.py"
SPEC = importlib.util.spec_from_file_location("repair_npx_shebang_bins", MODULE_PATH)
repair = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(repair)


class RepairNpxShebangBinsTest(unittest.TestCase):
    def test_makes_shebang_bin_executable_and_ignores_the_rest(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            pkg = root / "abc123" / "node_modules" / "hostinger-api-mcp" / "src" / "servers"
            pkg.mkdir(parents=True)
            js = pkg / "hosting.js"
            js.write_text("#!/usr/bin/env node\nconsole.log('ok')\n")
            js.chmod(0o644)
            bin_dir = root / "abc123" / "node_modules" / ".bin"
            bin_dir.mkdir(parents=True)
            (bin_dir / "hostinger-hosting-mcp").symlink_to(js)
            other = pkg / "readme.txt"
            other.write_text("no shebang\n")
            other.chmod(0o644)

            count = repair.repair_npx_shebang_bins(root)

            self.assertEqual(count, 1)
            self.assertTrue(js.stat().st_mode & 0o111)
            self.assertFalse(other.stat().st_mode & 0o111)

    def test_skips_already_executable(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            pkg = root / "abc123" / "node_modules" / "pkg" / "bin"
            pkg.mkdir(parents=True)
            script = pkg / "cli.js"
            script.write_text("#!/usr/bin/env node\n")
            script.chmod(0o755)
            bin_dir = root / "abc123" / "node_modules" / ".bin"
            bin_dir.mkdir(parents=True)
            (bin_dir / "cli").symlink_to(script)

            self.assertEqual(repair.repair_npx_shebang_bins(root), 0)


if __name__ == "__main__":
    unittest.main()

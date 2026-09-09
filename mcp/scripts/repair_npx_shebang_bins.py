#!/usr/bin/env python3
"""Linux: bins do npx com shebang precisam de +x. Sem isso o Cursor vê Permission denied."""

from __future__ import annotations

import os
from pathlib import Path

HOME = Path.home()
NPX_ROOT = HOME / ".npm" / "_npx"


def repair_npx_shebang_bins(npx_root: Path) -> int:
    if not npx_root.is_dir():
        return 0
    repaired = 0
    for bin_dir in npx_root.glob("*/node_modules/.bin"):
        if not bin_dir.is_dir():
            continue
        for entry in bin_dir.iterdir():
            target = entry.resolve() if entry.is_symlink() else entry
            if not target.is_file():
                continue
            try:
                with target.open("rb") as handle:
                    head = handle.read(2)
            except OSError:
                continue
            if head != b"#!":
                continue
            mode = target.stat().st_mode
            if mode & 0o111:
                continue
            target.chmod(mode | 0o111)
            repaired += 1
    return repaired


def main() -> None:
    count = repair_npx_shebang_bins(NPX_ROOT)
    print(f"npx shebang bins: {count} reparado(s)")


if __name__ == "__main__":
    os.umask(0o022)
    main()

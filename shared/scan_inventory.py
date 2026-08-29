#!/usr/bin/env python3
"""Inventário estrutural para /principios-audit.

Não julga arquitetura — lista o que existe para a varredura não ser amostragem.
Limites de SRP: os da constituição (AGENTS.md). Exclui gerado/vendored.

    python scan_inventory.py [repo_root]
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

SKIP_DIRS = {
    ".git",
    ".hg",
    ".svn",
    ".venv",
    "venv",
    "node_modules",
    "dist",
    "build",
    "coverage",
    "__pycache__",
    ".next",
    ".turbo",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    "vendor",
    "target",
    "bin",
    "obj",
    "graphify-out",
}
SKIP_FILE_PARTS = {
    "migrations",
    "generated",
    "snapshots",
    ".pb.go",
    "_pb2.py",
    ".min.js",
}
CODE_EXT = {".py", ".ts", ".tsx", ".js", ".jsx", ".go", ".cs", ".java", ".rs"}
LIMITS = {
    "function": 50,
    "class": 200,
    "domain_file": 250,
    "application_file": 300,
    "presentation_file": 250,
    "adapter_file": 400,
    "test_file": 500,
    "other_file": 400,
}
INFRA_HINTS = (
    "fastapi",
    "flask",
    "django",
    "starlette",
    "sqlalchemy",
    "prisma",
    "redis",
    "boto3",
    "botocore",
    "celery",
    "nest",
    "express",
    "typeorm",
    "sequelize",
    "axios",
    "requests",
    "httpx",
    "psycopg",
    "pymongo",
    "stripe",
    "react",
    "next",
    "langgraph",
    "langchain",
)
LAYER_PATH = (
    ("test", ("/tests/", "/test/", "__tests__", ".test.", ".spec.")),
    ("core", ("/core/", "/domain/", "/ports/")),
    ("application", ("/application/", "/usecase/", "/use_cases/", "/app/")),
    ("infrastructure", ("/infrastructure/", "/adapters/", "/infra/")),
    ("presentation", ("/presentation/", "/api/", "/controllers/", "/handlers/", "/runtimes/")),
)


def should_skip(path: Path) -> bool:
    parts = set(path.parts)
    if parts & SKIP_DIRS:
        return True
    s = str(path).lower()
    return any(p in s for p in SKIP_FILE_PARTS)


def detect_layer(path: Path) -> str:
    n = "/" + str(path).replace("\\", "/").lower() + "/"
    for layer, hints in LAYER_PATH:
        if any(h in n for h in hints):
            return layer
    return "other"


def file_limit(layer: str) -> int:
    return {
        "core": LIMITS["domain_file"],
        "application": LIMITS["application_file"],
        "infrastructure": LIMITS["adapter_file"],
        "presentation": LIMITS["presentation_file"],
        "test": LIMITS["test_file"],
        "other": LIMITS["other_file"],
    }[layer]


def count_lines(text: str) -> int:
    return text.count("\n") + (0 if text.endswith("\n") or not text else 1)


def py_units(text: str, path: str) -> list[dict]:
    units = []
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return units
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            end = getattr(node, "end_lineno", node.lineno)
            kind = "class" if isinstance(node, ast.ClassDef) else "function"
            units.append(
                {
                    "kind": kind,
                    "name": node.name,
                    "file": path,
                    "start": node.lineno,
                    "end": end,
                    "lines": end - node.lineno + 1,
                }
            )
    return units


FUNC_RE = {
    ".ts": re.compile(r"^(\s*)((?:async\s+)?(?:function\s+\w+|\w+\s*\([^)]*\)\s*:\s*\w+\s*=>|\w+\s*=\s*(?:async\s*)?\([^)]*\)\s*=>))", re.M),
    ".js": re.compile(r"^(\s*)((?:async\s+)?function\s+\w+)", re.M),
    ".go": re.compile(r"^func\s+", re.M),
    ".cs": re.compile(r"^\s*(public|private|protected|internal).*\([^;]*\)\s*\{", re.M),
}


def rough_units(text: str, path: str, ext: str) -> list[dict]:
    lines = text.splitlines()
    hits = []
    for i, line in enumerate(lines, 1):
        if ext in (".ts", ".tsx", ".js", ".jsx") and re.search(
            r"\b(function|=>)\b", line
        ):
            if line.strip().startswith("//"):
                continue
            hits.append(i)
        elif ext == ".go" and line.startswith("func "):
            hits.append(i)
        elif ext == ".cs" and re.search(r"\b(public|private|protected)\b.*\(", line) and "{" in line:
            hits.append(i)
    units = []
    for idx, start in enumerate(hits):
        end = (hits[idx + 1] - 1) if idx + 1 < len(hits) else len(lines)
        units.append(
            {
                "kind": "function",
                "name": f"L{start}",
                "file": path,
                "start": start,
                "end": end,
                "lines": end - start + 1,
            }
        )
    return units


def imports_of(text: str, ext: str) -> list[str]:
    found = []
    if ext == ".py":
        for m in re.finditer(r"^\s*(?:from|import)\s+([a-zA-Z0-9_\.]+)", text, re.M):
            found.append(m.group(1).split(".")[0].lower())
    else:
        for m in re.finditer(r"""from\s+['\"]([^'\"]+)['\"]""", text):
            found.append(m.group(1).split("/")[0].lstrip("@").lower())
        for m in re.finditer(r"""require\(['\"]([^'\"]+)['\"]\)""", text):
            found.append(m.group(1).split("/")[0].lstrip("@").lower())
    return found


def shingles(text: str, size: int = 10) -> dict[str, list[int]]:
    lines = [re.sub(r"\s+", " ", ln.strip()) for ln in text.splitlines()]
    lines = [ln for ln in lines if ln and not ln.startswith(("#", "//", "*", "/*"))]
    out: dict[str, list[int]] = defaultdict(list)
    if len(lines) < size:
        return out
    for i in range(len(lines) - size + 1):
        block = "\n".join(lines[i : i + size])
        digest = hashlib.sha1(block.encode()).hexdigest()[:12]
        out[digest].append(i + 1)
    return out


def classify_file(path: Path, repo: Path, text: str) -> dict:
    rel = str(path.relative_to(repo))
    layer = detect_layer(path)
    ext = path.suffix.lower()
    nlines = count_lines(text)
    if ext == ".py":
        units = py_units(text, rel)
    else:
        units = rough_units(text, rel, ext)
    over_fn = [u for u in units if u["kind"] == "function" and u["lines"] > LIMITS["function"]]
    over_cls = [u for u in units if u["kind"] == "class" and u["lines"] > LIMITS["class"]]
    imps = imports_of(text, ext)
    leaks = sorted({i for i in imps if i in INFRA_HINTS}) if layer in {"core", "application"} else []
    return {
        "file": rel,
        "layer": layer,
        "lines": nlines,
        "limit": file_limit(layer),
        "over_file": nlines > file_limit(layer),
        "functions_over": over_fn,
        "classes_over": over_cls,
        "infra_imports": leaks,
        "n_functions": sum(1 for u in units if u["kind"] == "function"),
        "n_classes": sum(1 for u in units if u["kind"] == "class"),
    }


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("root", nargs="?", default=".", type=Path)
    args = p.parse_args()
    repo = args.root.resolve()
    files = []
    shingle_index: dict[str, list[tuple[str, int]]] = defaultdict(list)
    for path in repo.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in CODE_EXT:
            continue
        if should_skip(path):
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        rec = classify_file(path, repo, text)
        files.append(rec)
        for digest, starts in shingles(text).items():
            for s in starts[:3]:
                shingle_index[digest].append((rec["file"], s))

    dupes = []
    seen_pairs = set()
    for digest, locs in shingle_index.items():
        uniq_files = {f for f, _ in locs}
        if len(uniq_files) < 2:
            continue
        pair = tuple(sorted(uniq_files))
        if pair in seen_pairs:
            continue
        seen_pairs.add(pair)
        dupes.append({"files": sorted(uniq_files), "example_lines": locs[:4]})

    files.sort(key=lambda r: (-int(r["over_file"]), -r["lines"]))
    summary = {
        "root": str(repo),
        "n_files": len(files),
        "over_file_limit": [f["file"] for f in files if f["over_file"]],
        "n_functions_over": sum(len(f["functions_over"]) for f in files),
        "n_layer_leaks": sum(len(f["infra_imports"]) for f in files),
        "n_duplicate_clusters": len(dupes),
        "limits": LIMITS,
    }
    out = {"summary": summary, "files": files, "duplicates": dupes[:80]}
    json.dump(out, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")


if __name__ == "__main__":
    main()

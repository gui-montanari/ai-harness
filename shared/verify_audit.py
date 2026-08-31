#!/usr/bin/env python3
"""Falha fechado quando o relatório contradiz as evidências da auditoria."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path


def fail(errors: list[str]) -> None:
    if errors:
        raise SystemExit("auditoria inválida:\n- " + "\n- ".join(errors))


def load(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SystemExit(f"não foi possível ler {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise SystemExit(f"{path} deve conter um objeto JSON")
    return value


def authority_exists(root: Path, source: str) -> bool:
    match = re.fullmatch(r"(.+):(\d+)", source)
    if not match:
        return False
    path = root / match.group(1)
    if not path.is_file():
        return False
    return int(match.group(2)) <= len(path.read_text(encoding="utf-8", errors="replace").splitlines())


def workspace_fingerprint(root: Path) -> str:
    diff = subprocess.run(
        [
            "git",
            "diff",
            "--binary",
            "HEAD",
            "--",
            ".",
            ":(exclude)docs/principles-audit/**",
            ":(exclude)docs/security-audit/**",
        ],
        cwd=root,
        capture_output=True,
        check=False,
    )
    untracked = subprocess.run(
        ["git", "ls-files", "--others", "--exclude-standard", "-z"],
        cwd=root,
        capture_output=True,
        check=False,
    )
    if diff.returncode != 0 or untracked.returncode != 0:
        return "unknown"
    digest = hashlib.sha256(diff.stdout)
    for raw in sorted(part for part in untracked.stdout.split(b"\0") if part):
        relative = raw.decode("utf-8", errors="surrogateescape")
        if relative.startswith(("docs/principles-audit/", "docs/security-audit/")):
            continue
        digest.update(b"\0" + raw + b"\0")
        path = root / relative
        if path.is_file():
            digest.update(path.read_bytes())
    return digest.hexdigest()


def suspicious_inventory(inventory: dict) -> set[str]:
    declared = inventory.get("audit_signals")
    if isinstance(declared, list):
        return {str(item.get("key")) for item in declared if item.get("key")}
    keys: set[str] = set()
    for record in inventory.get("files", []):
        file = record.get("file", "")
        if record.get("over_file"):
            keys.add(f"over_file::{file}")
        for unit in record.get("functions_over", []):
            keys.add(f"function_over::{file}:{unit.get('start')}")
        for unit in record.get("classes_over", []):
            keys.add(f"class_over::{file}:{unit.get('start')}")
        for module in record.get("infra_imports", []):
            keys.add(f"infra_import::{file}::{module}")
        for smell in record.get("runtime_smells", []):
            keys.add(f"runtime_smell::{file}::{smell}")
    for index, _cluster in enumerate(inventory.get("duplicates", [])):
        keys.add(f"duplicate::{index}")
    for signal in inventory.get("deploy", {}).get("signals", []):
        keys.add(f"deploy::{signal.get('file')}::{signal.get('kind')}")
    return keys


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--findings", type=Path, required=True)
    parser.add_argument("--evidence", type=Path, required=True)
    parser.add_argument("--coverage", type=Path, required=True)
    parser.add_argument("--inventory", type=Path)
    args = parser.parse_args()
    root = args.root.resolve()
    findings = load(args.findings)
    evidence = load(args.evidence)
    errors: list[str] = []

    commands = evidence.get("commands") or []
    if not commands:
        errors.append("evidence.json não possui gates executados")
    names = [item.get("name") for item in commands]
    if len(names) != len(set(names)):
        errors.append("nomes de gates duplicados")
    command_hints = {
        "lint": r"\b(lint|ruff|eslint)\b",
        "typecheck": r"\b(typecheck|mypy|pyright|tsc)\b",
        "test": r"\b(test|pytest|vitest|jest)\b",
        "architecture": r"\b(architecture|import-linter|lint-imports|dependency-cruiser)\b",
        "migrations": r"\b(migrations?|alembic|prisma)\b",
        "build": r"\b(build|docker)\b",
        "deploy": r"(compose.+config|helm.+lint|validate-deploy)",
    }
    for item in commands:
        if item.get("required", True) and item.get("exit_code") != 0:
            errors.append(f"gate obrigatório vermelho: {item.get('name')} (exit={item.get('exit_code')})")
        if not item.get("output_sha256"):
            errors.append(f"gate sem hash de saída: {item.get('name')}")
        executable = str(item.get("command", "")).strip().split(" ", 1)[0]
        if executable in {"", ":", "true", "echo", "printf"}:
            errors.append(f"gate não executa verificação real: {item.get('name')}")
        hint = command_hints.get(str(item.get("name")))
        if hint and not re.search(hint, str(item.get("command", "")), re.I):
            errors.append(f"comando não corresponde ao gate {item.get('name')}: {item.get('command')}")
    audit_kind = args.findings.parent.name
    required_names = {"lint", "typecheck", "test", "architecture"}
    if audit_kind == "principles-audit":
        required_names.update({"migrations", "build"})
    has_compose = any(
        path.name.lower() in {"compose.yml", "compose.yaml"} or path.name.lower().startswith("docker-compose")
        for path in root.rglob("*.y*ml")
        if "docs/principles-audit" not in str(path) and "docs/security-audit" not in str(path)
    )
    if has_compose:
        required_names.add("deploy")
    missing_commands = sorted(required_names - set(names))
    if missing_commands:
        errors.append(f"gates obrigatórios não executados: {', '.join(missing_commands)}")
    current_fingerprint = workspace_fingerprint(root)
    if current_fingerprint == "unknown":
        errors.append("não foi possível identificar a árvore git auditada")
    elif evidence.get("working_tree_sha256") != current_fingerprint:
        errors.append("evidence.json pertence a outra versão da árvore; execute os gates novamente")

    try:
        coverage = args.coverage.read_text(encoding="utf-8")
    except OSError as exc:
        errors.append(f"coverage ausente: {exc}")
        coverage = ""
    if not coverage.strip():
        errors.append("coverage vazio")
    if "| revisado | revisado |" in coverage:
        errors.append("coverage genérico 'revisado' não prova disposição por categoria")

    authorities = evidence.get("authorities") or []
    for authority in authorities:
        if not authority_exists(root, str(authority.get("source", ""))):
            errors.append(f"fonte de autoridade inválida: {authority.get('source')}")
    public_surfaces: set[str] = set()
    for line in coverage.splitlines():
        if "publico-intencional" not in line:
            continue
        tokens = re.findall(r"`([^`]+)`", line)
        routes = [token for token in tokens if token.startswith("/") or " /" in token]
        public_surfaces.add(routes[-1] if routes else (tokens[-1] if tokens else line.strip()))
    authorized_surfaces = {str(item.get("surface")) for item in authorities}
    for surface in sorted(public_surfaces - authorized_surfaces):
        errors.append(f"superfície pública sem requisito/ADR citado: {surface}")

    if args.inventory:
        inventory = load(args.inventory)
        expected = suspicious_inventory(inventory)
        dispositions = evidence.get("inventory_dispositions") or []
        given = {str(item.get("key")) for item in dispositions}
        for item in dispositions:
            if item.get("status") not in {"finding", "false_positive", "n/a"}:
                errors.append(f"disposição inválida: {item.get('key')}")
            if not str(item.get("reason", "")).strip():
                errors.append(f"disposição sem razão: {item.get('key')}")
        missing = sorted(expected - given)
        if missing:
            errors.append(f"{len(missing)} sinais do inventário sem disposição: {', '.join(missing[:5])}")

    if not isinstance(findings.get("findings"), list):
        errors.append("findings.json não possui lista findings")
    fail(errors)
    print("auditoria verificada: evidências, cobertura e gates coerentes")


if __name__ == "__main__":
    main()

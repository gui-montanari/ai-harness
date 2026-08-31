from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from shared import scan_inventory, verify_audit


class ScanInventoryTest(unittest.TestCase):
    def test_application_detecta_import_interno_de_infrastructure(self) -> None:
        root = Path("/repo")
        record = scan_inventory.classify_file(
            root / "src/pkg/application/use_case.py",
            root,
            "from pkg.infrastructure.di.container import Platform\n",
        )
        self.assertEqual(record["infra_imports"], ["pkg.infrastructure.di.container"])

    def test_application_permanece_livre_de_import_do_core(self) -> None:
        root = Path("/repo")
        record = scan_inventory.classify_file(
            root / "src/pkg/application/use_case.py",
            root,
            "from pkg.core.ports import Store\n",
        )
        self.assertEqual(record["infra_imports"], [])

    def test_frontend_app_nao_e_application_backend(self) -> None:
        root = Path("/repo")
        record = scan_inventory.classify_file(
            root / "frontend/web/src/app/App.tsx",
            root,
            "import React from 'react'\n",
        )
        self.assertEqual(record["layer"], "frontend")
        self.assertEqual(record["infra_imports"], [])

    def test_signal_fornece_chave_estavel_para_disposicao(self) -> None:
        root = Path("/repo")
        record = scan_inventory.classify_file(
            root / "src/pkg/application/use_case.py",
            root,
            "from pkg.infrastructure.repo import Repo\n",
        )
        signals = scan_inventory.audit_signals([record], [], {"signals": []})
        self.assertEqual(
            signals[0]["key"],
            "infra_import::src/pkg/application/use_case.py::pkg.infrastructure.repo",
        )


class VerifyAuditTest(unittest.TestCase):
    def green_commands(self) -> list[dict]:
        return [
            {"name": name, "command": f"make {name}", "exit_code": 0, "required": True, "output_sha256": "x"}
            for name in ("lint", "typecheck", "test", "architecture")
        ]

    def init_repo(self, root: Path) -> None:
        (root / "docs").mkdir(parents=True, exist_ok=True)
        (root / "AGENTS.md").write_text("# contrato\n", encoding="utf-8")
        (root / "docs/requisitos.md").write_text("# requisitos\nrota pública aprovada\n", encoding="utf-8")
        subprocess.run(["git", "init", "-q"], cwd=root, check=True)
        subprocess.run(["git", "config", "user.email", "audit@example.invalid"], cwd=root, check=True)
        subprocess.run(["git", "config", "user.name", "Audit Test"], cwd=root, check=True)
        subprocess.run(["git", "add", "."], cwd=root, check=True)
        subprocess.run(["git", "commit", "-qm", "fixture"], cwd=root, check=True)

    def run_verify(self, root: Path, coverage: str, evidence: dict) -> subprocess.CompletedProcess[str]:
        self.init_repo(root)
        audit_dir = root / "docs/security-audit"
        audit_dir.mkdir(parents=True, exist_ok=True)
        findings = audit_dir / "findings.json"
        evidence_path = audit_dir / "evidence.json"
        coverage_path = audit_dir / "coverage.md"
        findings.write_text('{"findings": []}', encoding="utf-8")
        evidence.setdefault("working_tree_sha256", verify_audit.workspace_fingerprint(root))
        evidence_path.write_text(json.dumps(evidence), encoding="utf-8")
        coverage_path.write_text(coverage, encoding="utf-8")
        return subprocess.run(
            [
                "python3",
                str(Path(__file__).with_name("verify_audit.py")),
                "--root",
                str(root),
                "--findings",
                str(findings),
                "--evidence",
                str(evidence_path),
                "--coverage",
                str(coverage_path),
            ],
            text=True,
            capture_output=True,
            check=False,
        )

    def test_reprova_gate_vermelho(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            result = self.run_verify(
                Path(tmp),
                "cobertura específica",
                {
                    "commands": [
                        {**item, "exit_code": 1} if item["name"] == "lint" else item
                        for item in self.green_commands()
                    ]
                },
            )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("gate obrigatório vermelho", result.stderr)

    def test_reprova_publico_sem_fonte(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            result = self.run_verify(
                Path(tmp),
                "| `POST /public` | coisa | publico-intencional |\n",
                {"commands": self.green_commands()},
            )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("sem requisito/ADR", result.stderr)

    def test_aceita_publico_com_fonte_e_gates_verdes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            result = self.run_verify(
                Path(tmp),
                "| arquivo | POST | `/public` | coisa | publico-intencional |\n",
                {
                    "commands": self.green_commands(),
                    "authorities": [
                        {"surface": "/public", "source": "docs/requisitos.md:2"}
                    ],
                },
            )
        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()

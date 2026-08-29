# Schema de `docs/principios-audit/findings.json`

O gerador `shared/generate_report.py` lê este JSON. Além dos campos comuns da auditoria de segurança, preencha `report`, `category_labels` e `category_order`.

```json
{
  "project_name": "acme-api",
  "date": "2026-08-29",
  "scope": "Repositório na branch main. src/ + tests/ + deploy/.",
  "methodology": "Constituição: AGENTS.md da raiz. Inventário via scan_inventory.py. Categorias mapeadas para src/core, src/application, src/infrastructure, api/.",
  "report": {
    "title": "Relatório de Auditoria de Princípios",
    "kicker": "SSOT · SRP · HEXAGONAL · TDD",
    "footer": "gerado por principios-audit",
    "filename": "relatorio-auditoria-principios.pdf"
  },
  "category_labels": {
    "ssot": "SSOT",
    "dry": "DRY / duplicação",
    "srp": "SRP / tamanho",
    "hexagonal": "Hexagonal",
    "tdd": "TDD",
    "dead_code": "Código morto",
    "yagni_kiss": "YAGNI / KISS"
  },
  "category_order": ["ssot", "dry", "srp", "hexagonal", "tdd", "dead_code", "yagni_kiss"],
  "stack": {
    "language": "Python 3.12",
    "framework": "FastAPI",
    "orm": "SQLAlchemy só em adapters",
    "auth": "JWT",
    "frontend": "React + Vite (repo irmão)",
    "deploy": ["Docker", "GitHub Actions"],
    "isolation_mechanism": "portas em core/; DI em infrastructure/di/"
  },
  "coverage_notes": {
    "ssot": "aplicável",
    "dry": "aplicável — N clusters do scanner revisados",
    "srp": "aplicável — limites da constituição",
    "hexagonal": "aplicável — camadas core/application/infrastructure",
    "tdd": "aplicável",
    "dead_code": "aplicável",
    "yagni_kiss": "aplicável"
  },
  "findings": [],
  "strengths": [],
  "weaknesses": [],
  "recommendations": [],
  "issues": []
}
```

Campos de cada finding: iguais à auditoria de segurança (`id`, `category`, `severity`, `file`, `lines`, `title`, `description`, `snippet`, `why_exploitable`, `exploitability_conditions`, `impact`, `fix`, `acceptance_criteria`).

Em princípios, `why_exploitable` = por que a violação **dói** (segundo dono, camada furada, teste que não protege).

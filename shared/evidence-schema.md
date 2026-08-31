# Evidence schema dos audits

`run_audit_checks.py` cria a base. O agente não altera `exit_code`, hashes ou saída; só
acrescenta autoridades e disposições verificadas.

```json
{
  "schema_version": 1,
  "root": "/repo",
  "commit": "git-sha",
  "working_tree_sha256": "sha256 do diff e arquivos não rastreados",
  "commands": [
    {
      "name": "lint",
      "command": "make lint",
      "required": true,
      "exit_code": 0,
      "duration_seconds": 4.2,
      "output_sha256": "sha256",
      "output_tail": "saída redigida"
    }
  ],
  "authorities": [
    {
      "surface": "/api/v1/public/cases/{token}",
      "source": "docs/requisitos.md:120"
    }
  ],
  "inventory_dispositions": [
    {
      "key": "infra_import::src/app/application/x.py::app.infrastructure.db",
      "status": "finding",
      "reason": "application importa adapter concreto; finding PR-004"
    }
  ]
}
```

Regras:

- `commands` vem exclusivamente do runner. Todo comando requerido precisa exit zero para o
  relatório final; durante a descoberta, vermelho vira finding e só fica verde após correção.
  Segurança exige os nomes `lint`, `typecheck`, `test`, `architecture`; princípios acrescenta
  `migrations` e `build`; se houver Compose, ambos exigem `deploy`. O comando pode ser o
  equivalente da stack, mas não `true`/`echo`/no-op.
- `authorities` cobre exatamente cada rota marcada `publico-intencional` em `coverage.md`.
  `source` aponta para requisito/ADR aceito, nunca README, teste ou implementação.
- `inventory_dispositions` cobre cada `inventory.json.audit_signals[].key`. `false_positive`
  e `n/a` exigem razão específica; “revisado” ou “não se aplica” sem prova não vale.
- O SHA auditado e o SHA dos gates devem representar a mesma árvore lógica. Se o código mudar,
  execute o runner e o verificador novamente.

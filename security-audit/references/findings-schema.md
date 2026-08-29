# Schema de `docs/security-audit/findings.json`

O gerador `scripts/generate_report.py` lê este JSON. Preencha todos os campos. Não deixe string vazia em `title`, `description` ou `severity`.

```json
{
  "project_name": "nome-do-repo",
  "date": "2026-08-29",
  "scope": "Repositório completo em <commit/branch>. Inclui backend, frontend, IaC e CI.",
  "methodology": "Parágrafo curto: stack detectada e como cada uma das 5 categorias foi mapeada.",
  "stack": {
    "language": "TypeScript",
    "framework": "Next.js 15 + NestJS",
    "orm": "Prisma",
    "auth": "JWT cookie httpOnly",
    "frontend": "Next.js App Router",
    "deploy": ["Dockerfile", "GitHub Actions", "Helm"],
    "isolation_mechanism": "filtro manual por organizationId no Nest; sem RLS"
  },
  "coverage_notes": {
    "banco_sem_tranca": "aplicavel | n/a — uma frase",
    "permissao_navegador": "aplicavel | n/a — uma frase",
    "idor": "aplicavel | n/a — N handlers inventariados",
    "chaves_expostas": "aplicavel | n/a — uma frase",
    "xss": "aplicavel | n/a — uma frase"
  },
  "findings": [
    {
      "id": "F-001",
      "category": "idor",
      "severity": "alta",
      "file": "apps/api/src/orders/orders.controller.ts",
      "lines": "42-58",
      "title": "GET /orders/:id devolve pedido de qualquer usuário",
      "description": "O handler busca o pedido só pela PK e não compara organizationId.",
      "snippet": "return this.prisma.order.findUnique({ where: { id } });",
      "why_exploitable": "Qualquer sessão autenticada lê o pedido de outro tenant conhecendo o UUID.",
      "exploitability_conditions": "Requer JWT válido. IDs UUID vazam na listagem do próprio tenant.",
      "impact": "Leitura cross-tenant de pedidos, clientes e valores.",
      "fix": "Após carregar, recusar se order.organizationId !== ctx.orgId (404).",
      "acceptance_criteria": [
        "GET com ID de outro tenant retorna 404",
        "Teste de integração cobre o caso cross-tenant"
      ]
    }
  ],
  "strengths": [
    {
      "title": "DELETE /orders/:id valida posse",
      "evidence": "Compara order.organizationId com o tenant do JWT antes do delete.",
      "file": "apps/api/src/orders/orders.controller.ts:90-104"
    }
  ],
  "weaknesses": [
    "Listagens e GET por ID não repetem o filtro de tenant que o DELETE já faz."
  ],
  "recommendations": [
    { "priority": "P1", "text": "Centralizar guard de tenant no Prisma middleware." },
    { "priority": "P2", "text": "Proibir defaults de JWT_SECRET no bootstrap." }
  ],
  "issues": [
    {
      "title": "[Segurança] GET /orders/:id sem checagem de tenant",
      "labels": ["security", "alta"],
      "body": "Markdown completo da issue (problema, evidência, impacto, correção, critérios de aceite)."
    }
  ]
}
```

## Categorias (`category`)

Use exatamente: `banco_sem_tranca` | `permissao_navegador` | `idor` | `chaves_expostas` | `xss`

## Severidade (`severity`)

Use exatamente: `critica` | `alta` | `media` | `baixa` | `informativa`

## Issues

Agrupe achados triviais relacionados numa issue única (ex.: vários defaults de segredo no mesmo tema). Cada issue:

- Título: `[Segurança] <descrição curta>`
- Labels: `security` + severidade
- Corpo em Markdown com: problema e por que é explorável; evidência `arquivo:linha` + trecho; impacto; sugestão de correção; critérios de aceite (checklist)

O gerador envolve cada issue com:

```
--- ISSUE n ---
...markdown...
--- FIM ISSUE n ---
```

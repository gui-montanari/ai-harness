# security-audit

Skill de auditoria de segurança em sete categorias, adaptada à stack do projeto. Gera relatório PDF em pt-BR e issues prontas para o GitHub.

Comando: `/security-audit`

## O que ela faz

1. Detecta a stack (linguagem, framework, ORM, auth, frontend, deploy) e o mecanismo de isolamento de tenant.
2. Audita:
   - **Isolamento de dados** — RLS/contexto global e posse
   - **Autorização** — ação, objeto, campo, impedimento e four-eyes
   - **IDOR e superfícies públicas** — todos os handlers; público com fonte aprovada
   - **Auth e sessão** — MFA, cookies/tokens, expiração, rotação e revogação
   - **Segredos e dados sensíveis** — hardcode, histórico, PII em banco/cache/evento/log/URL
   - **Inputs e injeção** — XSS, SQL/command/template injection, SSRF e path traversal
   - **Abuso e disponibilidade** — rate limit, paginação, tamanho, timeout e replay
3. Reporta só achados verificados no código (`arquivo:linha` + trecho).
4. Escreve `docs/security-audit/relatorio-auditoria-seguranca.pdf` com gráficos, tabela de achados e issues copiáveis.

## Uso

No repositório a auditar, com esta skill instalada:

```
/security-audit
```

ou: “Revisa este código atrás de falhas de segurança.”

O agente copia `shared/generate_report.py` e `shared/verify_audit.py` para
`docs/security-audit/`; o PDF só nasce com `evidence.json`, cobertura e gates verdes.

## Regenerar o PDF

```bash
cd docs/security-audit
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt   # copiado de shared/
.venv/bin/python generate_report.py findings.json
```

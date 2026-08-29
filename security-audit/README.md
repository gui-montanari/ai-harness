# security-audit

Skill de auditoria de segurança em cinco categorias, adaptada à stack do projeto. Gera relatório PDF em pt-BR e issues prontas para o GitHub.

Comando: `/security-audit`

## O que ela faz

1. Detecta a stack (linguagem, framework, ORM, auth, frontend, deploy) e o mecanismo de isolamento de tenant.
2. Audita:
   - **Banco sem tranca** — RLS ausente ou queries sem filtro de dono/org
   - **Permissão definida no navegador** — UI esconde, servidor não valida
   - **IDOR** — todos os handlers de rota, não amostras
   - **Chaves expostas** — hardcoded, defaults, git history, bundle
   - **Inputs sem tratamento (XSS)** — HTML perigoso no front e nos templates
3. Reporta só achados verificados no código (`arquivo:linha` + trecho).
4. Escreve `docs/security-audit/relatorio-auditoria-seguranca.pdf` com gráficos, tabela de achados e issues copiáveis.

## Uso

No repositório a auditar, com esta skill instalada:

```
/security-audit
```

ou: “Revisa este código atrás de falhas de segurança.”

O agente copia `scripts/generate_report.py` para `docs/security-audit/` do projeto auditado e gera o PDF em um venv local (nada global).

## Regenerar o PDF

```bash
cd docs/security-audit
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python generate_report.py findings.json
```

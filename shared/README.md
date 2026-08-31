SSOT de ferramentas das auditorias.

- `generate_report.py` — PDF A4 (segurança e princípios). Títulos e categorias vêm do JSON.
- `scan_inventory.py` — inventário estrutural para `/principles-audit` (stdlib).
- `run_audit_checks.py` — executa gates declarados e grava `evidence.json` com exit code e hash.
- `verify_audit.py` — reprova gate vermelho, cobertura genérica, sinal sem disposição e rota pública sem fonte.
- `evidence-schema.md` — contrato do `evidence.json` compartilhado pelos dois audits.
- `test_audit_tools.py` — testes stdlib do scanner e do verificador.
- `requirements.txt` — reportlab + matplotlib, só para o PDF; instalar em venv.

# principios-audit

Varredura de princípios: SSOT, DRY, SRP, hexagonal, TDD, código morto, YAGNI/KISS, segurança arquitetural, escala/desacoplamento (workers vs microsserviço), resiliência (auto-recovery, DLQ, idempotência).

Comandos: `/principios-audit` · `/hexagonal-audit`

A constituição (limites, camadas, processo) vive em [`../AGENTS.md`](../AGENTS.md). Este skill só descreve **como auditar**.

## Uso

No repositório-alvo, com a skill instalada:

```
/principios-audit
```

O agente lê o `AGENTS.md` do projeto (ou o template), roda `shared/scan_inventory.py` para não amostrar, confirma cada suspeita no código e gera `docs/principios-audit/relatorio-auditoria-principios.pdf`.

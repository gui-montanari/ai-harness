# principles-audit

Varredura de princípios: SSOT (global → herda), DRY, SRP, hexagonal, TDD, código morto, YAGNI, segurança, escala, resiliência, runtime (async-only, tenant, semáforo, retry, idempotência), consistência (nomes da indústria, schema ≠ entity ≠ record).

Comando: `/principles-audit`  
Aliases: `/principios-audit` · `/hexagonal-audit`

A constituição (limites, camadas, processo) vive em [`../AGENTS.md`](../AGENTS.md). Este skill só descreve **como auditar**.

## Uso

No repositório-alvo, com a skill instalada:

```
/principles-audit
```

O agente lê o `AGENTS.md` do projeto (ou o template), roda `shared/scan_inventory.py` para não amostrar, confirma cada suspeita no código e gera `docs/principles-audit/relatorio-auditoria-principios.pdf`.

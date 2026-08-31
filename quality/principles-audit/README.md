# principles-audit

Varredura de princípios: SSOT (global → herda), DRY, SRP, hexagonal, TDD, código morto, YAGNI, segurança, escala, resiliência, runtime (async-only, tenant, semáforo, retry, idempotência), consistência (nomes, schema ≠ entity ≠ record, Pydantic em `presentation/schemas/`, `/api/v1`, `backend/`/`frontend/`, migrations `YYYYMMDD_VV`).

Comando: `/principles-audit`  
Aliases: `/principios-audit` · `/hexagonal-audit`

A constituição (limites, camadas, processo) vive em [`../AGENTS.md`](../AGENTS.md). Este skill só descreve **como auditar**.

## Uso

No repositório-alvo, com a skill instalada:

```
/principles-audit
```

O agente lê o `AGENTS.md` e as fontes superiores do projeto, roteia as capacidades para as
skills especializadas, roda o inventário e os gates reais em `evidence.json`. O PDF só é
gerado depois que `shared/verify_audit.py` confirma gates verdes e todas as disposições.

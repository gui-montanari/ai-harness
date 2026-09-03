---
description: Contrato publicado, breaking change ou trava nova — pergunte antes, com o quê e o porquê.
alwaysApply: true
---

# Pergunte antes de contrato ou trava

Vale em todo projeto e todo host. Cliente pode apertar (overlay); não afrouxa.

**Pare e pergunte** — não edite no mesmo fôlego — se o recorte:

- muda **contrato publicado** (HTTP, evento, payload, campo compartilhado, schema que outro time/sistema consome);
- é **breaking** (remove, renomeia, torna obrigatório, muda semântica);
- acrescenta **trava** (guarda que para o fluxo, rejeita documento, bloqueia fila, fail-closed novo na borda).

No chat, **antes** do patch, em 4 linhas:

1. O que muda.
2. Quem consome.
3. O que acontece hoje sem isso.
4. Por que agora.

Espere o “pode” **deste** turno. Autorização de **editar um repo** não cobre contrato/trava. Refator interno de tipo privado, teste, ou trava que só o dono do fato já exige no mesmo bounded context: esta rule não dispara.

Stockfy: overlay `stockfy-repos-autorizacao` (time, `stockfy-integracao`, anti-corruption no `stockfy-ai`).

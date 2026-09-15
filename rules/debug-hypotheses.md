---
description: Defeito exige hipóteses concorrentes, tentativa de refutação e causa antes de qualquer patch.
alwaysApply: true
---

# Debug por hipóteses

Vale em todo projeto e todo host. HOW: skill `debug-hypotheses`.
Aplica quando o trabalho é **defeito, falha, regressão, teste vermelho ou comportamento inesperado**. Feature nova sem sintoma: esta rule não substitui `analyze-before-implement`.

- **Stop-the-line.** Sintoma novo: pare de acrescentar feature, preserve evidência (log, repro, saída do teste), diagnostique, só então o patch. Não empurre o próximo recorte com o teste vermelho.
- **Sem causa, sem patch.** “É provavelmente X” não autoriza editar X.
- **Hipóteses no chat**, antes da primeira correção: 2–4 concorrentes, cada uma com um teste que a **refutaria** (não que a confirmaria).
- **Refutar primeiro.** Rode o teste mais barato. Hipótese morta sai. Não empilhar mudanças para “ver se passa”.
- **A que sobrevive é a causa de trabalho.** Só então TDD no dono do fato. Sintoma (retry, `|| true`, if de defesa) não substitui a causa.
- Evidência (log Azure, trace, repro) pode vir de skill de cliente; o **método** é este.

Pedido e skill do recorte: `analyze-before-implement`. Worktree: `git-activity`.

---
name: debug-hypotheses
description: >
  Use when debugging a defect, test failure, regression, unexpected behavior,
  or production incident; when forming or refuting hypotheses; when verification
  (browser, log, Langfuse, API) shows an exception, KeyError, persistence/gravação
  failure, or a process step that did not occur — even if the UI looks ok or
  “não bloqueia o clique”; or when the user mentions debug, root cause,
  /debug-hypotheses. Not analyze-before-implement (pedido/skill). Not observability
  (how to log). Not a client `debug` skill (how to fetch Azure/WMS logs).
---

# Debug por hipóteses

**REQUIRED BACKGROUND:** rule `debug-hypotheses` (o gate). Esta skill é o HOW.
TDD depois da causa: constituição §1. Dono do fato: SSOT.

Skill de cliente chamada `debug` (logs Azure, etc.) é **fonte de evidência**, não este método.

## 1. Sintoma, não causa

No chat, uma linha: o que quebra, onde aparece, desde quando, como reproduzir.
Sem reprodução e sem evidência: colete (teste, log, request, diff recente). Não chute o arquivo.

## 2. Hipóteses concorrentes

Antes de qualquer patch, escreva 2–4 hipóteses **disjuntas o bastante para morrer sozinhas**:

```
H1: …  — morre se …
H2: …  — morre se …
H3: …  — morre se …
```

O “morre se” é uma observação barata (assert, query, um request, um `git bisect` de um arquivo). Teste que só **confirma** (“se eu ver X no log, é isso”) é viés. Queremos o teste que, se passar do outro jeito, **mata** H.

Uma hipótese só, ou “é o cache / é o tenant / é a rede” sem teste, é violação.

## 3. Refutar, da mais barata para a mais cara

Uma variável por vez. Hipótese refutada: risque no chat. Não “corrija H1 e H2 juntas para ver”.

Se **todas** morrerem: novas hipóteses com a evidência nova. Não volte ao shotgun.

Três tentativas de patch que revelam um problema **em outro lugar** a cada vez: pare. Isso é arquitetura (`architecture`), não o próximo if.

## 4. Causa → conserto assertivo

A hipótese que sobrevive é a causa de trabalho. Declare-a em uma frase. Aí:

1. Teste que falha **nessa causa** (não no sintoma genérico).
2. Patch **só** no dono do fato.
3. O teste passa; regressão em volta checada.

Retry, timeout maior, `except: pass`, flag, “tratar o erro na UI” sem a causa = sintoma.

## 5. Verificação que acha falha

Se o teste como usuário, o log, o Langfuse ou a API revelar exceção, `KeyError`, falha de gravação ou passo do processo que não ocorreu: **pare de declarar pronto.** Isto é o sintoma. Volte ao passo 1. Rule `complete-until-done`: conferência com gap observado não fecha.

## Red flags

- Patch na primeira impressão (“deve ser o Redis”)
- Várias mudanças num diff “de debug”
- Hipótese única sem teste de morte
- Skill de log do cliente usada como se já fosse a causa
- Corrigir o caller porque o dono do fato é difícil
- “Observação (não bloqueia o clique)” com exception no log
- Conferência `complete-until-done` toda `[x]` com falha vista na sessão

## Conferência

Antes de declarar pronto, copie e marque. Caixa vazia = falta.

- [ ] Sintoma e reprodução/evidência escritos antes do patch
- [ ] ≥2 hipóteses no chat, cada uma com teste que a refutaria
- [ ] Refutações rodadas; mortas riscadas; sem shotgun
- [ ] Causa sobrevivente em uma frase; teste que falha nela; patch no dono
- [ ] Sem conserto de sintoma no lugar da causa
- [ ] Falha vista na verificação não ficou como “observação”; conferência `complete-until-done` só fecha depois da correção

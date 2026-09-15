---
name: debug-hypotheses
description: >
  Use when debugging a defect, test failure, regression, unexpected behavior,
  or production incident; when forming or refuting hypotheses; or when the
  user mentions debug, root cause, /debug-hypotheses. Not analyze-before-implement
  (pedido/skill). Not observability (how to log). Not a client `debug` skill
  (how to fetch Azure/WMS logs).
---

# Debug por hipóteses

**REQUIRED BACKGROUND:** rule `debug-hypotheses` (o gate). Esta skill é o HOW.
TDD depois da causa: constituição §1. Dono do fato: SSOT.

Skill de cliente chamada `debug` (logs Azure, etc.) é **fonte de evidência**, não este método.

## Stop-the-line

Quando algo inesperado aparece:

1. **Pare** de acrescentar feature ou o próximo recorte.
2. **Preserve** evidência (saída do teste, log, repro).
3. Diagnostique (hipóteses abaixo).
4. Conserte a causa; **guarde** com o teste que falharia se o bug voltasse.
5. Só então retome.

Não empurre um teste vermelho ou build quebrado para “terminar o slice”.

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

## Quando não usar

- Pedido/skill antes de implementar: `analyze-before-implement`.
- Como logar/tracar: `observability`.
- Como buscar log Azure/WMS: skill `debug` de cliente.

## Desculpas que não valem

| Desculpa | Realidade |
|----------|-----------|
| É o Redis | Hipótese sem teste de morte. |
| Pressa: patch agora, hipóteses depois | Stop-the-line. Preservar evidência. |
| Três patches “para ver” | Shotgun. Pare; é arquitetura. |

## Red flags

- Patch na primeira impressão (“deve ser o Redis”)
- Várias mudanças num diff “de debug”
- Hipótese única sem teste de morte
- Skill de log do cliente usada como se já fosse a causa
- Corrigir o caller porque o dono do fato é difícil

## Conferência

Antes de declarar pronto, copie e marque. Caixa vazia = falta.

- [ ] Stop-the-line: evidência preservada; sem patch no meio de outro recorte
- [ ] Sintoma e reprodução/evidência escritos antes do patch
- [ ] ≥2 hipóteses no chat, cada uma com teste que a refutaria
- [ ] Refutações rodadas; mortas riscadas; sem shotgun
- [ ] Causa sobrevivente em uma frase; teste que falha nela; patch no dono
- [ ] Sem conserto de sintoma no lugar da causa; guarda contra recidiva

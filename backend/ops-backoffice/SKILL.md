---
name: ops-backoffice
description: >
  Use when designing or implementing an internal operations backoffice, support
  inbox, ticket/case queue, triage, assignment, SLA, operator reply, or when
  the user mentions backoffice, fila institucional, protocolo, or /ops-backoffice.
  UI: frontend-backoffice. Auth: auth. HTTP: http-apis.
---

# Backoffice operacional

Workspace **interno** para o time de suporte/operação tratar itens de trabalho (ticket, caso, protocolo). Não é o admin do framework, não é a superfície pública, não é um segundo backend.

**REQUIRED BACKGROUND:** constituição `AGENTS.md` §3 e §8. **REQUIRED SUB-SKILL:** `auth`, `http-apis`, `persistence-ports`. UI: `frontend-backoffice`. Fila/SLA que vaza do request: `background-workers`.

O dono do dado continua o bounded context do item (casos, conversas de suporte, …). Este skill é o **ecossistema**: fila, atribuição, transição, auditoria, projeção. Pasta `/tickets` como “serviço” é achado.

## Invariantes

- Nenhum item confirmado some por falha de roteamento. Sem dono individual → **fila institucional**.
- Authz **deny-by-default**, no servidor, por ação + objeto + campo. Esconder botão não autoriza.
- Sessão autenticada não concede `list/read/assign/resolve`: cada ação exige policy explícita,
  escopo organizacional e projeção de campos permitida.
- Papel suficiente **não** basta se o operador é parte do item (impedimento). Recusa fechada e auditada.
- Protocolo humano ≠ primary key ≠ token público. Lista operacional nunca autentica o titular.
- Identidade de canal / cofre **não** aparece na tela comum. Reidentificação é caso de uso privilegiado, mínimo, auditado, sem copiar o segredo no log.
- Projeção pública (o que o titular vê) ≠ vista interna. Nota, responsável e apuração não vazam.
- Transição é use case com versão lida (escrita condicional). `PATCH {status}` solto é achado.
- Autor e revisor vêm de principals autenticados distintos. `reviewer_id` recebido no body
  nunca satisfaz four-eyes nem vira identidade de auditoria.
- Toda atribuição, reatribuição, leitura sensível, exportação e encerramento gera auditoria append-only **sem** copiar conteúdo confidencial.

## Recorte

```
presentation/http/v1/ops/     # lista, detalhe, ações — sem regra
application/                  # AssignItem, TransitionItem, ReplyItem, CloseItem
core/domain/                  # Item, Protocol, Assignment, Queue, SlaClock
core/ports/                   # ItemRepository, AssignmentPolicy, AuditPort, Clock
infrastructure/adapters/
```

Lista, detalhe e ação chamam o **mesmo** use case que o worker de watchdog. SPA só consome `/api/v1`.

## Fila e item

| Campo na lista | Pode | Não pode |
|----------------|------|----------|
| Protocolo, status, fila, aging/SLA, updated_at, assignee opaco | sim | — |
| Relato integral, PII de canal, nota interna, identidade do cofre | — | nunca na lista |

Filtros no **servidor**: status, fila (`needs_reply` / `waiting` / `all`), assignee, aging. **`all` / Todos inclui triagem**. O filtro `triage` restringe à coleta em andamento, sem responsável. Paginação estável a um instante. Ordem: quem espera resposta primeiro, depois `updated_at`. Confirmação da coleta promove o item a aberto (`open`) na fila institucional, ainda sem dono.

Toda listagem possui teto e cursor/página estável. `list_all()` na rota operacional é achado,
mesmo que o volume inicial seja pequeno.

Detalhe: timeline de **fatos** (atribuído, respondido, aguardando, resolvido). Composer de resposta só se `can_reply`. Encerrar/resolver é transição, não delete.

Atribuição: exclusiva por item; autor, motivo, instante. Atribuir a um responsável **move o status para Em atendimento** (`in_progress`) no servidor. Automática (worker single-flight) **depois** da triagem e do impedimento — nunca para “não deixar vazio” em alguém inelegível. Reatribuição manual prevalece. Watchdog: item sem dono ou parado além do SLA alerta e escala (`background-workers`).

Resposta visível ao titular: se o domínio exige four-eyes, o autor **não** publica; fica pendente de revisor distinto. Ausência de revisor não libera publicação.

## Superfície

App interno distinto da home pública: sessão, cookie, CSP, `noindex`. Permissão `access_backoffice` **e** permissão da ação. Staff do framework / `is_superuser` não é o canal operacional.

Outbound (e-mail, WhatsApp, …) pelo porto de mensageria do **item**, não pelo handler HTTP.

## Red flags

- Django Admin / equivalente como fila do suporte
- Lista com JOIN no banco de outro serviço
- `status` mutável no cliente ou no handler
- Operador vê telefone/relato porque “está no backoffice”
- Item sem dono e sem fila institucional
- Dois operadores no mesmo item sem exclusividade
- Sessão genérica autorizando toda ação; `reviewer_id`/`actor_id` confiado do body
- UPDATE de transição sem `WHERE id = ? AND version = ?`
- Fila sem paginação/teto
- Auditoria que grava o corpo da mensagem

## Conferência

Antes de declarar pronto, copie e marque. Caixa vazia = falta.

- [ ] Item no bounded context dono; sem nanosserviço `/tickets`
- [ ] Fila institucional; atribuição exclusiva + auditada; impedimento na authz
- [ ] Lista: protocolo/status/SLA; sem corpo confidencial
- [ ] Transição por use case + versão; teste RED
- [ ] Authz no servidor por ação/objeto/campo; sessão ≠ autorização; sessão ≠ pública; `noindex`
- [ ] Autor/revisor derivados de principals distintos; nenhum ID de ator confiado do body
- [ ] Lista paginada com ordem estável e teto
- [ ] Four-eyes se o domínio exigir resposta pública
- [ ] Watchdog de SLA em worker, não no request
- [ ] UI pela skill `frontend-backoffice`

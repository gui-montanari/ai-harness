---
name: frontend-backoffice
description: >
  Use when building the authenticated operations UI: support inbox, ticket
  list and detail, triage queue, assignment, SLA badges, operator reply, or
  when the user mentions backoffice inbox, protocolo, or /frontend-backoffice.
  Shell: frontend-shell. Login: frontend-login. Backend: ops-backoffice.
---

# UI do backoffice operacional

SPA **interna** para o time de suporte ver e tratar a fila. Tokens e tema: `frontend-surfaces`. Chrome: `frontend-shell`. Login: `frontend-login`. Contrato e authz: `ops-backoffice` + `auth`. `ui/` não faz `fetch`.

Não é a home pública. Não é o admin do framework. Sessão, CSP e `noindex` próprios.

## Quadro

```
[ AppSidebar 260 | topbar + main ]
  Início              [ filtros ]     [ protocolo · status · SLA ]
  Fila / Atendimento  lista itens  |  timeline
  (outras seções      cards           ações + composer
   se o domínio
   autorizar)
  spacer
  UserMenu (sul)
```

**REQUIRED SUB-SKILL:** `frontend-shell` (sidebar, UserMenu no sul, tema no menu, idioma no topbar). Esta skill é o **miolo operacional**.

## Inbox (master-detail)

Nasce split, como a lista de chat — mas é **fila de trabalho**, não conversas do assistente.

```
[ filtros + lista ~320 | detalhe ]
  Abertos / Fechados / Todos
  Cliente aguarda / Aguardando titular
  card: protocolo, status, hora
  empty do filtro
                         header do item + ações
                         timeline
                         composer (se can_reply)
                         empty “Selecione um protocolo”
```

- **Cabeça da página:** eyebrow interno, H1 “Atendimento” (i18n), métrica `N ativos` — número vem da API, não conta DOM.
- **Filtros:** links/chips, um ativo visível, query no servidor (`?status=&queue=`). Não filtrar o relato no cliente.
- **Card:** protocolo em destaque, status (dot + rótulo), `updated_at` curto. **Sem** trecho do relato se o domínio for confidencial. Preview de última mensagem só quando o item não carrega conteúdo protegido.
- **Ativo:** borda/fundo `--action`. Clique troca o detalhe **sem** perder o filtro.
- **Empty do filtro:** “Nenhum protocolo neste filtro.” Empty do detalhe: “Selecione um protocolo” — a conversa não mistura dados entre itens.
- **Paginação** estável (cursor/página da API). Scroll da lista não carrega o mundo.

&lt;900px: lista em tela cheia; detalhe em rota própria ou drawer. Não esconda filtros.

Catálogo, histórico tabular, afiliados, qualquer listagem **sem** split: `DataTable` da skill `frontend-surfaces`. Um vocabulário. Não invente uma segunda tabela nesta SPA.

## Detalhe

Header: protocolo, status, assignee (nome operacional, **não** identidade de canal), aging/SLA. Ações só as que o **servidor** já autorizou na projeção (`can_reply`, `can_close`, `can_assign`). Botão invisível ≠ permissão.

Timeline: fatos em ordem, autor operacional, instante. Nota interna e cofre **não** renderizam a menos que a API os entregue para este principal.

Composer: textarea do design system (min-height 48, um anel). Enviar chama `lib/api.ts`. Item encerrado = somente leitura, copy i18n, sem composer.

SLA: badge com token `--ok` / `--action` / `--danger` segundo a faixa **que a API mandou**. Front não calcula deadline.

Atribuição: select/dropdown do **mesmo** vocabulário do `UserMenu`. Destino inelegível nem aparece (a API não lista).

## O que a tela não faz

- Não autoriza. 403 da API → estado de erro uniforme, não “tente de novo”.
- Não busca por conteúdo confidencial no cliente.
- Não mostra telefone, relato integral ou token em URL, tooltip ou `title`.
- Não usa a paleta pública cream/hero. `data-surface="internal"`.
- Não importa o `ConversationThread` de produto-chat para o ticket — o thread operacional é timeline + composer desta skill. Chat de produto (`frontend-chat`) é outra superfície.

## Viewport, i18n, tema

Herdados: light/dark, PT/EN, `dvh`, toque 44px. `robots noindex`. Verificar 375 / 768 / 1280 **e** os dois temas com um item aberto, um filtro vazio e um 403.

## Red flags

- Tabela CRUD com o relato na célula
- Filtro só no `array.filter` do JSON completo
- Composer visível em item que a API marcou read-only
- Dois shells (um do app e um “do suporte”)
- Session da home pública neste bundle
- Badge de SLA pintado com hora local inventada no front
- Django Admin / equivalente embutido no nav como “fila”

## Conferência

Antes de declarar pronto, copie e marque. Caixa vazia = falta.

- [ ] SPA interna + `frontend-shell`; UserMenu no sul; tema/idioma nativos
- [ ] Inbox split: filtros servidor + lista de protocolo/status/hora (card, não tabela)
- [ ] Listagem tabular (se houver) usa `DataTable` tokenizado (`frontend-surfaces`)
- [ ] Detalhe: timeline do **item selecionado**; sem misturar
- [ ] Ações só com flag da API; 403 tratado
- [ ] Sem relato/PII na lista se o domínio for confidencial
- [ ] Composer no design system; encerrado = read-only
- [ ] `lib/api.ts` + tipos do contrato; zero `fetch` no `ui/`
- [ ] 375 / 768 / 1280 e os dois temas conferidos
- [ ] Sessão/CSP/`noindex` distintos da home pública

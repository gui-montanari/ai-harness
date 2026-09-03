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
[ AppSidebar 260 | main 100% da altura restante ]
  Operação
    Conversas → /cv
  spacer
  UserMenu (sul: tema, idioma, sair)
```

**REQUIRED SUB-SKILL:** `frontend-shell` (sidebar fixa, tópicos/subtópicos, path por folha, toggle de painel, UserMenu no sul com tema **e** idioma). Esta skill é o **miolo operacional**. Sem topbar de chrome no bloco central.

Rota da jornada no **browser**: **`/cv`** e **`/cv/:caseId`**. Duas letras quando o menu cresce (`/us`, `/ft`, `/pf`). A API permanece `/api/v1/backoffice/cases`. Label: “Conversas”. Aliases `/c` e `/conversations` redirecionam.

## Inbox (master-detail)

Nasce split, **casca de chat**: lista à esquerda rola; o thread à direita tem altura **fixa no viewport** e o compositor **sempre visível**. Não é o assistente de produto (`frontend-chat`); não importe `ConversationThread`.

```
[ busca + funil + lista ~320 | thread ]
  Conversas                         header (protocolo · status)
  Buscar... [funil]                 bolhas (relato / respostas)
  Status | Atribuição               [ flex:1 overflow-y ]
  Tópico | Subtópico                composer preso embaixo
  card: protocolo, status
  empty do filtro                   empty “Selecione uma conversa”
```

- **Host:** `.inbox-page` preenche o `main` (`height: 100%; min-height: 0`). O `app-content` **não** rola a página no desktop/tablet. Lista: `overflow-y: auto`. Thread: coluna flex — header / mensagens (`flex: 1; min-height: 0; overflow-y`) / composer (`flex-shrink: 0`). Composer fora da tela porque o split cresceu com o conteúdo é achado.
- **Composer:** form arredondado, textarea auto-resize (teto 160px), Enter envia, Shift+Enter quebra, botão enviar sempre no sul do thread. Tokens `--chat-*`. Um anel no form (`focus-within`), não no textarea.
- **Cabeça da lista:** rótulo “Conversas”. Sem H1 duplicando o chrome. Sem contador de ativos na cabeça.
- **Filtros:** recolhidos por padrão. Ícone de funil **à direita** da busca, na mesma linha; respiro abaixo do rótulo “Conversas”. O grid abre **abaixo** da linha busca+funil. Query no servidor (`?q=&status=&assignment=&topic_id=&subtopic_id=`). Status do funil vem do catálogo (`/backoffice/statuses`). **Todos inclui Triagem**; o filtro `triage` restringe à coleta em andamento. Dropdowns são `MenuSelect` (`.menu-pop`), nunca `<select>` nativo. Desktop: linha 1 Status + Atribuição, linha 2 Tópico + Subtópico. Funil com ponto quando algum filtro não é o default.
- **Triagem:** card com protocolo, badge `--warn` (amarelo), sem responsável. A primeira mensagem inbound já abre o protocolo. Mensagens da coleta entram no thread à medida que o canal responde. Confirmação da coleta **promove** para Em aberto (`open`), ainda sem dono.
- **Tempo real:** a página abre `EventSource` em `/api/v1/backoffice/cases/live` (sessão cookie, `case:list`). O evento é um ping numérico, sem conteúdo. A página refaz lista e thread ativo. Regra completa: skill `frontend-chat` (tempo real). `ui/` não abre stream.
- **Administrativo** só no nav de `dap` / `technical_admin`. Usuários: lista + `+` para criar; editar e-mail, nome, papel e ativo. Filtros de Conversas: catálogo de status, tópicos e subtópicos. Filtros **nascem recolhidos**; clique na linha do filtro expande as opções. Opção filha **não** mostra estado — só editar (e “—” na coluna de adicionar opção). Modal de editar: dropdown absoluto não dispara scrollbar no cartão. Perfil: e-mail somente leitura; o dono não troca o e-mail — só o admin. Botão Salvar do perfil é compacto (`form-actions`), não faixa full-width.
- **Modal** (exportação, editar, histórico) cobre **toda** a viewport, inclusive a sidebar: o backdrop é `position: fixed` no `document.body` (portal). Overlay que deixa o nav à mostra é achado.
- **Card:** protocolo em destaque, status (dot + rótulo). Triagem usa variante `warn`. **Sem** trecho do relato se o domínio for confidencial.
- **Ativo:** borda/fundo `--action`. Clique troca o thread **e** o path `/cv/:id` sem perder o filtro.
- **Empty:** “Nenhuma conversa neste filtro.” / “Selecione uma conversa”.
- **Paginação** estável. Scroll da lista não carrega o mundo.
- **Exportação / download em massa:** ícone abre **modal** de confirmação (baixar / cancelar). Clique único que dispara o arquivo é achado.
- Campos de contato, busca, catálogo e compositor: `maxLength` alinhado ao schema HTTP. Telefone em País/DDD/número, largura do campo cabe o teto. Nome e e-mail compactos (não `1fr`) — sem faixa em branco.

&lt;900px: lista **ou** thread (rota `/cv/:id` + voltar). Composer continua preso. Send ≥ 44px. Não empilhar lista+thread numa página que rola o compositor para fora.

Catálogo, histórico tabular, afiliados, qualquer listagem **sem** split: `DataTable` da skill `frontend-surfaces`. Um vocabulário. Não invente uma segunda tabela nesta SPA.

## Detalhe

Header: protocolo, status, assignee (nome operacional, **não** identidade de canal), aging/SLA. Ícone de histórico **à direita do protocolo** abre modal com a timeline da API (abertura, atribuição, status, encerramento: quem, para quem, quando). Ações só as que o **servidor** já autorizou na projeção (`can_reply`, `can_close`, `can_assign`). Botão invisível ≠ permissão.

Timeline: fatos em ordem, autor operacional, instante — abertura, atribuição, status, **filtro/opção**, encerramento. Sem corpo de mensagem, relato ou cofre. Nota interna **não** renderiza a menos que a API os entregue para este principal.

Composer: o mesmo vocabulário do chat (form + send). Enviar chama `lib/api.ts`. Item encerrado = somente leitura, copy i18n, sem composer.

SLA: badge com token `--ok` / `--action` / `--danger` segundo a faixa **que a API mandou**. Front não calcula deadline.

Atribuição: select/dropdown do **mesmo** vocabulário do `UserMenu`. Destino inelegível nem aparece (a API não lista).

## O que a tela não faz

- Não autoriza. 403 da API → estado de erro uniforme, não “tente de novo”.
- Não busca por conteúdo confidencial no cliente.
- Não mostra telefone, relato integral ou token em URL, tooltip ou `title`.
- Não usa a paleta pública cream/hero. `data-surface="internal"`.
- Não importa o `ConversationThread` de produto-chat. A **casca** (lista rolável + thread de altura fixa + compositor preso) é desta skill; o assistente de produto (`frontend-chat`) é outra superfície.

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
- Jornada de conversas em `/conversations`, `/helpchat` ou `/hc` na barra
- Página inteira rolando e o input de enviar sumindo no desktop/tablet
- Download da fila no primeiro clique, sem modal
- Input gravável sem `maxLength`
- `Todos` listando item em triagem
- Stream de inbox com corpo de mensagem ou PII
- Polling da fila quando o ping SSE já existe

## Conferência

Antes de declarar pronto, copie e marque. Caixa vazia = falta.

- [ ] SPA interna + `frontend-shell`; UserMenu no sul com tema e idioma; sem topbar de chrome
- [ ] Path `/cv` e `/cv/:id`; label Conversas; tokens de duas letras por jornada
- [ ] Inbox split: lista rolável + thread de altura fixa; compositor sempre visível
- [ ] Inbox split: filtros servidor + lista de protocolo/status/hora (card, não tabela)
- [ ] Listagem tabular (se houver) usa `DataTable` tokenizado (`frontend-surfaces`)
- [ ] Detalhe: timeline do **item selecionado**; sem misturar
- [ ] Ações só com flag da API; 403 tratado
- [ ] Sem relato/PII na lista se o domínio for confidencial
- [ ] Composer no design system; encerrado = read-only
- [ ] `lib/api.ts` + tipos do contrato; zero `fetch` no `ui/`
- [ ] 375 / 768 / 1280 e os dois temas conferidos
- [ ] Sessão/CSP/`noindex` distintos da home pública
- [ ] Download da fila com modal de confirmação
- [ ] Inputs graváveis com teto igual ao da API
- [ ] Triagem em Todos e no filtro próprio; badge amarelo; sem dono; promove a Em aberto na confirmação
- [ ] SSE de invalidação na página; refetch; sem conteúdo no evento

---
name: agent-orchestration
description: >
  Use when creating, scaffolding, or birthing a product agent, changing
  ConversationalSpec, GraphSpec, WorkflowSpec, conversational vs operational
  flow, conversational/engine, specs/job, graph.py, node.py, edge.py,
  config.py, prompts folder, prompts/guardrails.md, prompts/reflection.md, canonical copy vs
  prompt, LLM protocol, provider, model, tencent, openai, deepseek,
  LLM-driven turn, specialist/sub-agent, agent config.py,
  LLM_API_KEY, LLM_BASE_URL, getenv, guards, guardrails, output guard,
  state guard, or reflection. Also AgentRegistry, registry.get, UnknownAgent,
  build_orchestration, CancelConversation, turn_idempotency, conversation_turns,
  executable agent HTTP endpoint, route_factory, allowed_specialist_keys,
  HubResolver, NodeType, ANALYSIS node, specs/job/schemas.py, structured
  output contract, FieldPatch, packages/contracts event from a graph.
  Activating Make/LangGraph/in-process: orchestration-runtime. MCP /mcp:
  mcp-servers + mcp-tools. LangGraph mention: langgraph-agents.
---

# Orquestração de agentes

O fluxo é **declarativo e neutro** (`ConversationalSpec` / `GraphSpec` / `WorkflowSpec`). O motor conversacional **recebe** o spec; o job concreto vive em `specs/<job>/`. Make.com, LangGraph ou outro runtime **compilam** o spec no adapter. O domínio não importa SDK de Make nem `StateGraph`.

Como o runtime de processo é escolhido e ligado no startup: skill `orchestration-runtime`. A pasta do spec é a mesma, qualquer que seja o adapter.

**REQUIRED BACKGROUND:** `AGENTS.md` hexagonal + `persistence-ports`. Banco e LLM são portas.

Nascer um agente — neste produto ou em qualquer outro — é a **receita abaixo**, no mesmo commit. Pular um passo = o agente **não nasceu**. Não existe “ligo a guarda depois” nem “reflection numa fase 2”.

## Um trabalho por conversacional — o registry já aceita N

O **registry nasce como mapa** (`get` / `keys` / `explicit((...))`): 1..N ids únicos, sem auto-discovery. Travar `len(specs) == 1` no tipo é o defeito que força um segundo PR só para cadastrar o visitor.

Quantos **registrar** = o requisito, não o tipo:

| Situação | O que nasce |
|----------|-------------|
| Um público, uma jornada (coleta confidencial) | um `specs/<job>/` |
| Dois públicos ou dois trabalhos (visitor vs interno; copiloto vs canal) | dois specs **já no primeiro lançamento**, cada um com a própria `allowed_specialist_keys` |
| Mesma jornada fatiada em `general` + `support` | **proibido** — um só trabalho cognitivo |

Não invente o segundo conversacional “para o futuro”. Se o requisito de agora tem um, registre um. Se tem dois, registre dois. O tipo aguenta os dois casos.

| Tentação | Por que não |
|----------|-------------|
| `general` roteando para `support` | um só trabalho cognitivo. “Agente geral para tudo” infla prompt, tools e risco |
| `specialist/support` como primeiro agente | specialist = pipeline operacional (documento, lote, job), não conversa. Escala humana **não** é outro LLM |
| Agente de escalonamento | HITL na **mesma** conversa ou fila de operação depois do fato de negócio. Determinístico |
| `AgentRegistry.explicit` que recusa `len != 1` | o segundo conversacional vira breaking change no core |

Escalonar para humano: `PendingInteraction` / atribuição de operador, não um segundo manifest. Depois do fato oficial: fila institucional, não agente.

Cada conversacional declara a própria allowlist de specialists. Sem pasta `specialists/` vazia.

## Allowlist por conversacional (hub)

Quando o produto tem o segundo gênero (pipeline operacional: documento, lote, wave), o conversacional **não** ganha todos os specialists. O descriptor do conversacional nasce com `allowed_specialist_keys: frozenset[...]` explícito.

| Peça | Contrato |
|------|----------|
| v1 sem specialist | `allowed_specialist_keys=frozenset()` — o LLM não recebe tool operacional |
| Specialist operacional | pasta própria (`specs/<job>/` ou `specialists/<domínio>/<key>/`); **não** é segundo conversacional |
| Allowlist | o conversacional lista as keys (ou padrão fechado) que **aquele** hub pode invocar |
| Resolver (application) | tools = allowlist do conversacional ∩ scopes do `Principal` ∩ allowlist do tenant (se o produto tiver capabilities por tenant) |
| Fora da lista | falha fechado — não vaza por prompt |
| Vários conversacionais | cada um com a **sua** lista (visitor ≠ general: onboarding não entra no hub interno) |
| Boot | literal para specialist inexistente/deprecated aborta; ciclo / profundidade acima do teto aborta; wildcard sem match = warning |
| Publicação | estar na allowlist **não** publica MCP/REST (`mcp-tools` / `http-apis`) |

`conversational.general` + `specialists/support` para a **mesma** jornada de coleta continua proibido. Hub + specialist operacional (outro bounded context, outro efeito) é o padrão escalável. Sem auto-discovery “todo specialist em todo hub”.

## Receita de nascimento

Mesmo commit. Ordem abaixo. Conferência vazia = não pronto.

1. **Identidade e registry.** Cada conversacional: id `conversational.<job>` + pasta `specs/<job>/` com `graph.py`, `node.py`, `edge.py`. Grafo com nó ANALYSIS: também `schemas.py` (um tipo de saída por nó). Operacional: bounded context próprio. `AgentRegistry.explicit((...))` — 1..N, ids únicos, sem auto-discovery, **sem** `len == 1`. API: `get(agent_id)` e `keys()`; id desconhecido **falha fechado**; tuple vazia ou id duplicado não registra. Composition: `spec = registry.get("conversational.<job>")` — não `registry.primary` como único sul. Manifest conversacional nasce com `requires_output_guard`; `False` não registra. `allowed_specialist_keys` no descriptor: vazio se aquele hub não invoca pipeline; explícito senão.
2. **Slots de prompt.** Em `specs/<job>/prompts/`: `guardrails.md` e `reflection.md` (H1 mínimo). Conversacional: `understand_turn.md` + `ask_*.md` por fase. Catálogo **não carrega** se faltar `guardrails` ou `reflection`. O catálogo **não** tem pasta default de um job — `register.py` passa o diretório.
3. **Duas casas.** Semântica nos `.md`. Legal / recusa / recap no domínio. Schema/enum no domínio. `PromptCatalog` é porta; core não lê disco; versão no trace.
4. **Contratos hexagonais.** No mesmo commit do spec. `NodeType` em cada `NodeSpec`. Nó `ANALYSIS` → tipo de saída em `specs/<job>/schemas.py` + LLM *structured output* nesse tipo (não `json.loads`/`dict`). Estado tipado. Command/Result do turno em `application/commands/`. Se o grafo **fecha um fato** de negócio: nome em `packages/contracts` + outbox (`reliable-messaging`). HTTP: `http-apis`. Secção «Caminho hexagonal do grafo».
5. **Guardas no caminho.** Estado (schema) + `inspect_outbound` / `approve_outbound` no texto **gerado**. Recusa canônica no domínio. Sem a chamada de saída, o agente não ativa.
6. **Sensibilizar.** A jornada chama `active("guardrails")` e `active("reflection")`. Vazio = no-op. Ausente = não sobe. Reflection nunca substitui a saída; revisão **reentra** em `inspect_outbound`.
7. **Config de LLM — protocolo, provider, modelo.** Três camadas. `protocol` é o **nome do dialeto** (`openai`, `tencent`, `deepseek`) — não um apelido genérico (`openai_chat_completions`) nem um `Callable`. Cada dialeto tem adapter próprio; Tencent não reusa a classe OpenAI. `provider` é quem hospeda (catálogo → URL default + protocolo esperado). `model_name` é o deployment. Protocolo incompatível com o provider **falha fechado**. Chave injetada no composition. `complete()` vazio é falha.
8. **Runtime.** Um adapter (`orchestration-runtime`). Factory `build_orchestration(...)` — sem locator global. Porta: `execute_turn` / `pause` / `resume` / `cancel`. `CancelConversation`: status `cancelled`; **não** publica nem fecha o fato oficial (caso, pedido, protocolo). Conversacional nasce com `turn_idempotency=True`; `ensure_compatible` no startup. Capabilities exigidas ⊂ oferecidas. Mesmo builder na API e no worker.
9. **Idempotência de turno.** Tabela `<bc>.conversation_turns` no serviço dono (em geral schema `agents`), RLS `FORCE`, PK `(tenant_id, conversation_id, idempotency_key)`. Replay pela key devolve o resultado gravado — não reexecuta o motor. A abertura (`prefix`) segue no reply ao canal; o turno **persistido** grava `prefix` vazio para o retry do canal não reenviar o opening. Porta `get_turn` / `save_turn`. HOW SQL: `persistence-ports` + `sql-migrations`.
10. **Superfície acionável.** Registro ≠ publicação. Se o agente é **executável** (alguém fora do grafo chama: humano, M2M, widget, host MCP, canal), o mesmo commit liga **pelo menos um** driving adapter escrito na apresentação — não `route_factory` no descriptor. Escolha a superfície do requisito: HTTP `/api/v1/...` (`http-apis`), MCP (`mcp-servers` + `mcp-tools`), canal (`whatsapp-channel`), consumer de evento (`reliable-messaging` + `background-workers`). `include_router` / publicação / inscrição **explícitos** no composition. Specialist só-tool do hub (o LLM chama; ninguém de fora) **não** ganha REST próprio. Sem isso o spec é teatro.
11. **Borda MCP no mesmo composition** se o produto tem (ou o requisito pede) conector. Não é fase 2. Streamable HTTP em `/mcp` no mesmo FastAPI (`mcp-servers`). Catálogo ≠ perfil (`mcp-tools`). `MCP_ENABLED` default off (lista vazia). Ligado: `MCP_BEARER` + `MCP_TENANT_ID` obrigatórios no startup; sem token → 401; `tenant_id` no body rejeitado. Binding = use case de turno (`open_conversation` + `execute_turn`). Sem canal WhatsApp, sem fato oficial. Se o requisito **nega** conector, não nasça `/mcp` teatro — registre a negação no ADR.
12. **Testes de nascimento** (senão é teatro): catálogo falha sem cada slot; heading-only → `active` é `None`; bloqueia reivindicação e permite abertura canônica; recap intacto **e** montado das labels do spec; registro rejeita tuple vazia, id duplicado e conversacional sem guarda de saída; `explicit` com **dois** ids distintos aceita; `get` de id desconhecido falha; `cancel` não fecha fato oficial; mesma `idempotency_key` replay idêntico e `prefix` persistido vazio; engine não importa spec concreto nem copy canônica; composição: `execute_turn` chama a guarda no gerado; `config.py` existe no spec; adapter de LLM sem `getenv` e sem prefixo da marca; cada contrato de ANALYSIS rejeita extra/invariante quebrada (e ignora `reply` se for extract de campos); se fecha fato: envelope em `packages/contracts` + outbox na mesma transação + `tests/contract` do publisher; se executável: a superfície (HTTP/MCP/canal/evento) responde no TestClient/consumer; se houver `/mcp`: 401 sem Bearer, `tools/list` só o perfil, `tenant_id` no body 400; se houver specialist: tool fora da allowlist do conversacional não resolve; boot falha com literal quebrado.

Ausência ou indisponibilidade de LLM/runtime é erro recuperável do turno: persiste pendência e
retoma idempotentemente. Nunca avança a coleta por formulário, regex ou pergunta canônica como
se tivesse compreendido linguagem livre. Capacidade declarada no manifest/contrato (voz, tool,
HITL) só fica ativa se adapter + capability check + caminho de execução + teste estiverem ligados.

Não abra PR / não declare pronto com item da conferência vazio.

## Caminho hexagonal do grafo

Nascer `graph.py` + `node.py` + `edge.py` **sem** os contratos das outras camadas é teatro: o motor anda, o produto não escala. O grafo é topologia. Cada nó que **analisa** (LLM ou heurística) devolve um **tipo fechado**. `dict` cru e `json.loads` no use case são o anti-padrão.

Indústria (LangGraph / PydanticAI / `with_structured_output`): estado do grafo **tipado** (`TypedDict` / dataclass / Pydantic); saída do LLM **amarrada a um schema** no adapter; plano sem efeito, depois executor determinístico; `extra="forbid"` no schema do modelo. `NodeType` **não** é API do LangGraph — é o mapa deste harness para esses papéis.

### NodeType (mapa deste harness)

No `NodeSpec` do `GraphSpec` / `WorkflowSpec` — não só `name`/`field`/`ask`:

| Tipo | Faz | Contrato de saída |
|------|-----|-------------------|
| `ANALYSIS` | Estrutura o que o modelo (ou uma função pura) **entendeu** | **Um tipo nomeado por nó** em `specs/<job>/schemas.py` |
| `STEP` | Transformação determinística; aplica plano; persiste | Valor de domínio / Command já tipado; não parseia JSON |
| `DECISION` | Roteia (`router` / token) | Enum/str do próprio `EdgeSpec` |
| `END` | Terminal | Nenhum efeito novo |

Coleta conversacional linear (`field` + `ask_*`) continua válida: o extract do turno **é** ANALYSIS (`FieldPatch` / equivalente). Mini-nós focados (um contrato cada) batem um `converse` god-object.

### Onde mora cada contrato

Papéis da constituição §3.1 — o grafo não inventa uma quinta casa.

| Contrato | Onde | É | Não é |
|----------|------|---|-------|
| Topologia | `core/domain/` (`GraphSpec`, `NodeType`) | dado | SDK |
| Saída de ANALYSIS | `specs/<job>/schemas.py` | borda do **modelo** (Pydantic/`extra="forbid"` aqui, como HTTP em `presentation/schemas/`) | schema HTTP; envelope de evento; `dict` no engine |
| Estado do grafo | `TypedDict` / dataclass que **estende** um `BaseState` (`status`, `error`) | campos = os tipos de ANALYSIS + acumulado do job | `state: dict` sem forma |
| Command / Result do turno | `application/commands/` | `ConductTurnCommand`, `TurnResult` | tuple de 4 elementos; schema HTTP |
| Plano sem efeito | o tipo ANALYSIS (`*Plan`, `*Output`) | o STEP executor aplica | tool com side-effect chamada direto pelo LLM no pipeline |
| Fato entre BCs | fábrica no produtor; **nome** em `packages/contracts` | outbox na mesma transação (`reliable-messaging`) | flag `*_completed` no result; tabela candidata de ADR |
| Schema HTTP | `presentation/schemas/` | `http-apis` | `schemas.py` do job |

`description=` nos `Field` do contrato de ANALYSIS **é** o que o modelo lê. Invariante (`approve` ⇔ `findings` vazio; `apply` ⇔ há `actions`) vive em `model_validator`, não no prompt.

LLM preenche o tipo no **adapter** (`output_type=ThatContract` / structured). O node devolve o valor (ou o mapper para o domínio). STEP consome o tipo — não reinterpreta string.

Contrato **externo** (payload de outro sistema, evento) é tipo **à parte**. Só é o mesmo objeto se o requisito disser que o payload **é** o contrato publicado.

Tabela de ADR “catálogo candidato” **não** é contrato. Até o `event_type` estar em `packages/contracts` e o outbox no use case, o grafo não fechou o fato.

### Completude

```
nó ANALYSIS → tipo em schemas.py → campo no state
fato de negócio → Command → outbox → packages/contracts → consumidor
```

Campo analisado que não chega ao state/fato = achado. Nó ANALYSIS sem tipo = achado.

## Dois gêneros (quando houver o segundo caso)

| | Conversacional | Operacional |
|--|----------------|-------------|
| Turnos | vários, pausa/retoma, HITL | pipeline com início e fim |
| Estado | sessão + histórico | documento / lote / job |
| LLM | conduz a conversa | um node; o resto determinístico |
| Exemplo de pasta | `specs/intake/` | `specs/document_extract/` |

Não invente árvore `specialists/` só para ter “cara de multi-agent”. Specialist operacional entra na **allowlist do conversacional** que pode invocá-lo. O segundo conversacional é **outra pasta em `specs/`** + ADR + a **própria** `allowed_specialist_keys`.

## Motor + specs (indústria)

Dois papéis, duas pastas. O motor **não** conhece o job. O job **não** reimplementa o motor. Prompts soltos na raiz do serviço = o segundo spec copia o primeiro.

```
agents/
  conversational/engine.py   # motor; percorre o grafo; não conhece o job
  core/domain/
    graph.py                 # ConversationalSpec / GraphSpec + AgentManifest
    node.py                  # NodeSpec + NodeType (ANALYSIS|STEP|DECISION|END)
    edge.py                  # EdgeSpec
  specs/<job>/               # um job = uma pasta
    schemas.py               # um tipo de saída por nó ANALYSIS; estado acumulado do job
    graph.py                 # monta SPEC (nós + arestas + copy)
    node.py                  # NODES + normalize
    edge.py                  # EDGES (token ou incondicional)
    config.py                # SSOT de LLM por node — sem getenv
    register.py              # composition: build_catalog() + exporta SPEC
    prompts/
      guardrails.md
      reflection.md
      understand_turn.md
      ask_*.md
```

SRP do job: **nó** muda quando o passo muda; **aresta** muda quando a transição muda; **grafo** monta o spec e a copy. Um `spec.py` único mistura os três motivos.

Arquivo só existe com corpo. `node.py` / `edge.py` / `graph.py` **vazios**, `specialists/`, porta de fala, `presentation/` sem consumidor = código morto.

`ConversationalEngine` segue arestas (`token` ou incondicional). Labels, opening e completed **vivem no spec**. O engine não importa `canonical_texts` nem `specs.<job>`.

`tools/` do grafo **não** entram em `tools/list` do MCP. Publicar capacidade ou jornada: skill `mcp-tools`. Rota REST do agente executável: skill `http-apis` — o spec **não** conhece FastAPI.

Quem **liga o processo** (in-process / Make / LangGraph) é `orchestration-runtime`. O motor conversacional interpreta o grafo no turno.

### Node e edge (vocabulário da indústria)

Grafo (LangGraph, StateGraph, cenário Make): **node** = unidade de trabalho; **edge** = transição. No in-process isso **é** dado, não função LangGraph:

| Grafo | Arquivo do job | Tipo de domínio |
|-------|----------------|-----------------|
| node | `specs/<job>/node.py` (`NODES`) | `NodeSpec` (`name`, `node_type`, e se coleta: `field`, `ask`, `label`) |
| ANALYSIS | `specs/<job>/schemas.py` | um tipo de saída por nó; LLM structured |
| edge | `specs/<job>/edge.py` (`EDGES`) | `EdgeSpec` (`source`, `target`, `token`) |
| wiring + copy | `specs/<job>/graph.py` (`SPEC`) | `ConversationalSpec` / `GraphSpec` |
| checkpointer | banco do serviço | `ConversationStore` |
| interrupt / HITL | use case | atribuição / `human_pending` |

`token=None` = aresta linear (depois de coletar o campo). `token="continuar"` / `"sim"` = aresta condicional. Nó sem `field` e sem aresta de saída = terminal.

Quando LangGraph é o runtime escolhido: `infrastructure/adapters/langgraph/` lê o **mesmo** `ConversationalSpec` (`nodes` + `edges`) e compila `StateGraph`. Um turno de usuário = um `ainvoke` (aresta para END). Banco do serviço continua SSOT — checkpointer do LangGraph não substitui `ConversationStore`. Não copie o grafo para um segundo `graph.py` com SDK. `from langgraph.graph import StateGraph` no spec, no engine ou no use case é defeito. Ponte: `langgraph-agents`.

Não crie `nodes/` extra “para quando o LangGraph chegar”. Função de node LLM só nasce com o adapter e o `LlmPort` ligados.

### Acrescentar um spec

O registry **já** é N. Acrescentar não muda o tipo.

1. Pasta `specs/<job>/` com `graph.py`, `node.py`, `edge.py`, slots, config, register. Nós ANALYSIS: `schemas.py` no mesmo commit.
2. Id novo, trabalho/audiência distintos dos já registrados. Mesma jornada com outro nome = defeito.
3. Append na tuple de `AgentRegistry.explicit`. Se for specialist operacional, **também** acrescente a key na `allowed_specialist_keys` **só** dos conversacionais que podem chamá-lo.
4. Composition resolve com `registry.get("conversational.<job>")`. Sem auto-discovery. Sem importar `SPEC` no use case. Sem `primary` como único caminho. Resolver de tools honra a allowlist no boot.
5. O motor já existe — **não** copie `engine.py`. Factory e `ensure_compatible` já ligam o runtime.

### Um runtime, um canal — não throwaway

LangGraph **agora** para “depois trocar por Make” = dois adapters descartáveis. Escolha **um** (`orchestration-runtime`) e compile o spec nele. In-process já orquestra o grafo de coleta. LangGraph entra quando a ADR o escolhe como **o** runtime — não como ensaio.

Canal de entrada **não** mora no serviço de agentes. WhatsApp: skill `whatsapp-channel`. Twilio, Evolution e qualquer outro webhook vivem em `messaging-gateway/infrastructure/adapters/<provider>/`, mesma porta, vocabulário neutro.

Cópia canônica (`canonical_texts` ou equivalente no domínio) **é** necessária: abertura legal, recusa da guarda, hold humano, enum de categoria. Não é obsoleto. Obsoleto é constante sem leitor (apaga).

Stub de fala que devolve transcrição inventada, porta sem caminho, `presentation/` que ninguém importa: não nascem. “Depois a gente liga” é ocupação.

## LLM-driven — duas casas de texto

Agente conversacional é **LLM-driven** no turno de modelo: o modelo compreende linguagem livre e **propõe** atualização estruturada. O estado, o schema, a confirmação e a criação do fato **não** são o modelo.

Misturar isso num `canonical_texts.py` com abertura legal **e** “qual é a obra?” é o anti-padrão: um módulo, dois motivos para mudar, e o modelo nunca entra.

| Casa | O que mora | Quem escreve na conversa |
|------|------------|--------------------------|
| `prompts/*.md` | instrução **semântica** ao modelo: tom, como compreender, como escolher a próxima lacuna, few-shot | o modelo, depois da guarda de saída |
| Cópia canônica no domínio | texto que tem de ser **byte-estável**: abertura legal, privacidade, direitos, opt-out, emergência, recusa da guarda, recap de confirmação, mídia não suportada | o sistema, sem passar pelo modelo |
| Schema / enum | categoria, campo, valor permitido | ninguém “redige”; valida |

O recap de confirmação monta-se do **estado estruturado** (a descrição é o texto do colaborador). Não se pede ao modelo para “resumir o caso”.

**Roteamento do turno:** clique em **elemento interativo** (payload estruturado do canal) → sem modelo. **Texto digitado é sempre turno de modelo**, mesmo quando a redação coincide com um rótulo (“Atraso de pagamento”, “Não sei”, “sim” num campo). Palavra mágica que dispensa o LLM quebra a premissa LLM-driven. Tokens de grafo (`continuar` na abertura, `sim` no recap, comandos de privacidade/direitos) continuam determinísticos: são opt-in legal e confirmação do fato, não vocabulário de campo. Classificar texto livre como clique é defeito bloqueante.

Turno de modelo:

1. `active("guardrails")` (se houver) + prompt da tarefa + versão no trace
2. `LlmPort` propõe **patch tipado** (`FieldPatch` / contrato de ANALYSIS — não `dict` solto). **Não** propõe a próxima fala.
3. Guarda de **estado** aceita ou rejeita o patch; o motor **aplica** só campos do schema, pula nó já preenchido e nó cujo `when` não casa, e para na **próxima lacuna**
4. A pergunta ao humano sai do `ask_*` **desse** nó (catálogo, ou paráfrase do modelo **amarrada** a esse slot). `reply` do extract **não** vira outbound
5. Se gerado e `active("reflection")`: passe de qualidade; revisão volta ao texto
6. Guarda de **saída** **sempre** no texto a entregar (depois da reflection)
7. Canônico, recap e eco de valor já confirmado **não** passam por geração, reflection nem guarda de geração — só se despacham

HITL de coleta (um turno = uma mensagem do canal):

| Quem | Faz | Não faz |
|------|-----|---------|
| Modelo | compreende linguagem livre e preenche slots do schema, inclusive vários numa mensagem | inventar campo, pular ordem, redigir a jornada, confirmar, criar o fato |
| Grafo | escolhe a próxima lacuna canônica; `when` no `NodeSpec` liga campo opcional a um valor já coletado | |
| `ask_*.md` | semente da pergunta daquela lacuna (script da jornada) | copy legal |
| Motor | aplica patch, pula preenchido, chega no `ask_*` devido | conhecer o job |

Inventar “cidade” quando a lacuna é obra, ou usar o `reply` do JSON do modelo no lugar do `ask_*` do grafo, é defeito bloqueante. Teste: fake devolve `{"fields": {"regional": "Sudeste"}, "reply": "Qual é a cidade?"}` → outbound contém a pergunta de **obra**, não “cidade”.

`PromptCatalog` é porta. Os `.md` carregam-se no composition root / adapter de arquivos. Domínio não lê disco. Versão (hash ou tag) registra-se em cada `AgentRun`. Sem I/O no `core/`.

Não coloque enum de categoria ou regra de confirmação no prompt. Política de nunca-prometer mora em `prompts/guardrails.md`; o matcher 100% mora em `inspect_outbound`. Não coloque “como perguntar a regional em linguagem natural” em constante Python.

## Config de LLM — protocolo ≠ provider ≠ modelo

Marca do produto no nome da variável (`ACME_LLM_TOKEN`) acopla o código ao tenant. Adapter que lê `os.environ` fura o composition root. `config.py` com a chave da API mistura segredo com política do node.

| Camada | Valor | Não é |
|--------|-------|--------|
| **Protocolo** | `openai` / `tencent` / `deepseek` (dialeto, um adapter cada) | `openai_chat_completions` genérico; `Callable`; classe OpenAI usada pela Tencent |
| **Provider** | quem hospeda; catálogo aponta o protocolo **esperado** | o id do modelo |
| **Modelo** | deployment nesse provider | a URL |

Hub agnóstico: o domain só vê `LlmPort.complete`. Trocar Tencent → DeepSeek nativo muda `protocol`+`provider`+chave no composition, não o use case. Envelope HTTP igual **hoje** não autoriza um protocolo só — se o dialeto divergir, muda um arquivo.

| Casa | Mora | Não mora |
|------|------|----------|
| `specs/<job>/config.py` | protocol, provider, model_name, temperatura, max_tokens **por node** | `getenv`, URL, token, prefixo da marca |
| Catálogo de providers (infra) | provider → protocolo + URL default | chave, regra de negócio |
| Settings (composition) | chave do provider escolhido | qual node usa qual modelo |
| Adapter (`LlmPort`) | HTTP do **protocolo**, URL/token/modelo **injetados** | `os.environ`, `complete()` vazio |

`LlmNodeConfig` é dataclass de domínio. Sem Pydantic no core. Sem `api_key` no config do node.

```
NODE_CONFIGS = {
    "llm_turn": LlmNodeConfig(
        temperature=0.2, max_tokens=4096,
        model_name="deepseek-v4-flash-202605",
        provider="tencent",
        protocol=LlmApiProtocol.TENCENT,  # valor = nome do dialeto
    ),
}
```

Não declare node LLM chamado `guardrails`. Sem chave no composition: **não** instancia o adapter.

Env: capacidade ou contrato de mercado do **provider**, nunca marca do produto.

| Ok | Defeito |
|----|---------|
| `LLM_API_KEY`, `OPENAI_API_KEY`, `DEEPSEEK_API_KEY`, `TENCENT_API_KEY` | `ACME_GPT_KEY`, `TENDA_LLM_TOKEN` |

A mesma regra vale para **todo** env e **schema SQL**, não só LLM: constituição §3.1. `agents.conversations` atrás de `ConversationStore`. Não `workspace.conversations` nem `TENDA_PG_*`.

## Guardas — montagem e uso

Três peças. Não são sinônimos. Biblioteca `guardrails` (SDK) é **adapter opcional**, nunca o dono da regra.

| Peça | Faz | Não faz | Quem implementa |
|------|-----|---------|-----------------|
| Guarda de **estado** | aceita ou rejeita o patch no schema (campo, fase, confirmação, criação do fato) | redigir a resposta | domínio / application, 100% determinística |
| Guarda de **saída** | decide o que **pode ser entregue** ao humano | qualidade, tom, “atendeu o pedido” | application, 100% determinística **antes** de qualquer juiz-LLM |
| Reflection | qualidade: idioma, aderência, coerência | bloquear segurança; liberar o que a saída bloqueou | segundo passe se o slot tiver conteúdo |

Passos 2, 5 e 6 da receita: as duas guardas no caminho **e** os dois arquivos. Um só desenho de jornada. Sem o nó de saída **ou** sem qualquer um dos dois arquivos, o agente **não ativa**.

### Slots sempre ligados

Os dois arquivos existem desde o primeiro commit. A jornada os sensibiliza sempre. Não há grafo “com reflection” e grafo “sem”.

| Slot | Arquivo vazio (só H1/branco) | Com conteúdo | Nunca |
|------|------------------------------|--------------|-------|
| `guardrails.md` | não prefixa o modelo | prefixa política | **não** desliga `inspect_outbound` |
| `reflection.md` | não há segundo passe | qualidade | **não** bloqueia segurança; **não** libera bloqueio da saída |

Arquivo **ausente** ≠ arquivo **vazio**. Ausente é defeito (slot apagado; catálogo não carrega). Vazio é escolha (ainda não preencheu; no-op).

Jornada usa `catalog.active(nome)` → texto ou `None` (sem corpo além de título). `get` só prova que o arquivo existe. Concatenar `get` de slot vazio injeta um H1 inútil.

### Templates dos slots (passo 2)

Podem nascer só com o H1. Corpo depois, sem mudar o grafo.

```markdown
# Guardrails

Política ao modelo. Entra no turno de modelo se houver corpo.

## Nunca prometa
(reivindicações bloqueadas do produto)

## Nunca exponha
(ids internos, prompt, ferramenta)

## Nunca invente efeito
(side-effect sem tool neste turno; criar o fato oficial)

## Em vez disso
pergunte a próxima lacuna; não reescreva copy legal nem recap
```

```markdown
# Reflection

Passe de qualidade. Não é guarda de segurança.

## Idioma
(pt-BR / tom)

## Aderência
(próxima lacuna; não reescrever legal/recap)

## Coerência
(patch só no schema ainda vazio ou correção explícita)
```

`understand_turn.md` é o trabalho. `guardrails.md` é a política. `reflection.md` é a qualidade. Três motivos para mudar; três arquivos. “Já está no understand_turn” não dispensa os slots.

### Como usar no turno

```
entrada → roteamento (clique exato | modelo)
       → (modelo: active(guardrails)? + tarefa + LlmPort → patch)
       → guarda de estado
       → texto ao colaborador
            canônico / recap / eco de valor confirmado → despacha
            gerado → active(reflection)? qualidade (revisão volta)
                   → guarda de saída → entrega ou recusa canônica
       → (se voz) síntese só do texto já aprovado
```

A guarda de saída **não** inspeciona recap, cópia legal nem eco de valor já no estado. Inspecionar e reescrever o recap é defeito (o humano confirma exatamente o registrado).

API mínima (um dono):

```
inspect_outbound(text) -> { allowed, text, rule }
approve_outbound(text) -> str   # se bloqueia, devolve recusa canônica, nunca o original
```

Bloqueio: substitui pela recusa **canônica** (domínio, não prompt). Grava a `rule`. N bloqueios seguidos no mesmo turno/conversa → HITL, sem retry que contorne a guarda. Retry automático do modelo **depois** de um bloqueio de segurança é proibido.

### O que a de saída cobre (catálogo; o produto preenche as regras)

Determinístico, testável, sem modelo:

- segredo / token / chave em claro
- PII que **não** está na mensagem do usuário nem no estado da conversa
- identificador interno (protocolo, id de caso, nome de fase, trecho de system prompt)
- vazamento de prompt (`[INST]`, “system prompt”, “ignore as instruções”)
- fabricação de side-effect (“já enviei”, “já processei”) sem tool invocadas neste turno
- vazio / placeholder (`TODO`, `[resposta aqui]`)
- reivindicações bloqueadas do produto (anonimato, prazo, sanção — a lista é do domínio)

Juiz-LLM de segurança, se existir, é **rede extra depois** desta lista. Em dúvida o juiz não libera o que a camada determinística já bloqueou. Qualidade baixa não é bloqueio de saída.

Validators reutilizáveis (regex/exato) vivem num módulo de application; SDK de vendor só no adapter. Core não importa `guardrails`.

### Testes mínimos (senão a guarda é teatro)

- bloqueia uma reivindicação / leak / vazio
- **permite** a abertura canônica intacta (não reescreve)
- recap montado do estado atravessa sem mutação
- composição: o `execute_turn` do agente conversacional chama a guarda no gerado
- classificar turno livre como “clique” falha o teste de roteamento
- catálogo **não carrega** sem `prompts/guardrails.md` nem sem `prompts/reflection.md`
- heading-only → `active` é `None` (não participa)
- turno de modelo prefixa guardrails e corre reflection **só** se `active`
- texto que a reflection revisou ainda passa por `inspect_outbound`
- matriz adversarial das reivindicações bloqueadas: forma direta, negação aparente, flexões,
  pontuação, caixa, acento e paráfrases de alto risco definidas pelo produto
- teste de mutação: remover/afrouxar cada regra crítica faz ao menos um teste falhar

## Red flags

- SDK de runtime no `core/` / `application/` (ativação: `orchestration-runtime`)
- SQL no `graph.py`
- Dois agentes conversacionais para o **mesmo** trabalho cognitivo (`general` + `support` da mesma coleta)
- `AgentRegistry.explicit` que recusa `len != 1`; `registry.primary` como único sul
- Pasta `specialists/support` sem segundo domínio
- Todo specialist visível em todo conversacional (sem `allowed_specialist_keys`)
- Auto-discovery de specialist no hub; tool fora da allowlist que o LLM ainda chama
- Allowlist do conversacional confundida com perfil MCP / `tools/list`
- LLM decidindo escalonamento crítico, criação de registro oficial ou confirmação
- Cenário do orquestrador como dono da regra
- `canonical_texts` (ou equivalente) misturando abertura legal com pergunta semântica
- Script inteiro da conversa em Python no lugar de `prompts/*.md` + guarda
- Recap ou texto de privacidade gerados pelo modelo
- Prompt como única cópia de categoria/enum
- Guarda de saída implementada só com LLM-juiz (“na dúvida passa”)
- Reflection (qualidade) usado como bloqueio de segurança
- Recap ou cópia legal reescritos pela guarda
- Retry de modelo após bloqueio de segurança
- SDK `guardrails` no `core/` / `application/`
- Agente declarado pronto sem a receita de nascimento completa
- `AgentRegistry.get` que devolve `None`; composition que importa `SPEC` em vez de `registry.get`
- Locator / singleton global no lugar de `build_orchestration`
- `cancel` que apaga conversa ou fecha o fato oficial
- `turn_idempotency=False` no conversacional; replay em `set()` na RAM
- Retry do canal reenvia opening (`prefix` regravado no turno persistido)
- MCP “numa fase 2” depois do spec “já funcionar”
- `route_factory` / `m2m_handler_factory` no descriptor (domínio conhecendo HTTP)
- Agente executável sem `include_router`, publicação MCP, canal ou inscrição de evento no composition
- Auto-discovery de rota por pasta do spec
- `MCP_ENABLED=true` sem `MCP_BEARER` + `MCP_TENANT_ID` no startup
- `graph.py` / `node.py` / `edge.py` **vazios**, ou um `spec.py` único misturando nó+aresta+copy
- Nó `ANALYSIS` sem tipo em `schemas.py`; `json.loads` / `dict` atravessando engine ou use case
- Um único BaseModel god para todos os nós ANALYSIS
- LLM com side-effect no pipeline: falta o tipo `*Plan` e o STEP executor
- Flag `*_completed` no `TurnResult` no lugar do fato em `packages/contracts` (quando outro BC consome)
- `schemas.py` do job misturado com `presentation/schemas/` HTTP
- Pasta `nodes/` / `specialists/` sem função que corre
- Stub de fala / porta / `presentation/` sem caminho de execução
- LangGraph (ou segundo runtime) como ensaio do Make
- Canal não oficial (Evolution, Baileys) como ensaio do provider do requisito
- `prompts/` na raiz do serviço de agentes (o job mora em `specs/<job>/prompts/`)
- Engine importando um spec concreto ou `canonical_texts`
- Labels de recap, opening ou completed cravados no motor
- `FilePromptCatalog` com pasta default de um job
- Copiar `engine.py` para o segundo spec
- Agente conversacional registrado sem guarda de saída no caminho do turno
- Manifest conversacional com `requires_output_guard=False`
- Agente sem `prompts/guardrails.md` ou sem `prompts/reflection.md`
- Dois grafos (com/sem reflection) em vez de slot vazio
- Política de nunca-prometer só em `understand_turn.md`
- `guardrails.md` vazio usado para pular `inspect_outbound`
- `get("reflection")` concatenado sem `active` (injeta H1 vazio)
- `guardrails.md` como única enforcement (sem `inspect_outbound`)
- Prefixo da marca em variável de LLM (`*_LLM_URL`, `*_LLM_TOKEN`)
- Adapter de LLM lendo `os.environ` / `getenv`
- Protocolo genérico (`openai_chat_completions`) para Tencent/DeepSeek
- `OpenAiProtocolLlm` servindo provider `tencent` (dialetos colapsados)
- Protocolo como `Callable` / função injetada no domínio
- `api_key` ou URL no `config.py` do agente
- Node LLM chamado `guardrails` no lugar de `inspect_outbound`
- `complete()` devolvendo vazio quando falta URL (fallback silencioso)
- ausência/falha de LLM avançando a coleta por pergunta determinística
- manifest anuncia voz/tool/HITL sem adapter ativo e teste de ponta a ponta
- guarda que bloqueia só frase literal e permite paráfrase óbvia da mesma promessa
- JSON de extract com `reply` usado como fala ao humano
- Motor que avança um campo por turno e não pula lacuna já preenchida
- Modelo inventando campo fora do `collect` do spec (cidade, CEP, documento…)
- `is_deterministic_collect` / matching de vocabulário digitado para pular o LLM

## Conferência

Antes de declarar pronto, copie e marque. Caixa vazia = o agente **não nasceu**.

- [ ] Identidade: um conversacional **por trabalho**; registry 1..N (`explicit` sem `len == 1`); pasta `specs/<job>/`; `get` falha fechado; composition via `registry.get`; `requires_output_guard`; `allowed_specialist_keys` explícito (vazio se não há specialist)
- [ ] Teste: dois ids distintos registram; duplicata e tuple vazia recusam
- [ ] Se há specialist: resolver ∩ scopes (± tenant); fora da lista falha; boot valida literal/ciclo; allowlist ≠ publicação MCP
- [ ] Contratos hexagonais: `NodeType` no spec; cada ANALYSIS com tipo em `schemas.py` + structured output; estado tipado; Command/Result em `application/commands/`; fato entre BCs em `packages/contracts` + outbox se o grafo fecha negócio
- [ ] Motor em `conversational/` recebe spec; job com `graph.py` + `node.py` + `edge.py` **com corpo**; engine sem import de job nem de copy canônica
- [ ] Factory `build_orchestration`; porta com `cancel`; `CancelConversation` não fecha fato oficial; `turn_idempotency=True`; `ensure_compatible` no startup
- [ ] `<bc>.conversation_turns` com RLS; replay pela key; `prefix` persistido vazio
- [ ] Borda MCP no mesmo commit **ou** ADR que nega conector; conferências `mcp-servers` + `mcp-tools` se `/mcp` existir
- [ ] Executável: um driving adapter explícito (HTTP / MCP / canal / evento) no mesmo commit; sem `route_factory` no spec
- [ ] Sem stub, porta ou presentation sem consumidor; sem segundo runtime/canal throwaway
- [ ] `specs/<job>/prompts/guardrails.md` e `reflection.md` no mesmo commit; catálogo falha sem qualquer um; catálogo sem pasta default de um job
- [ ] Duas casas: semântica nos `.md`; legal/recusa/recap e schema no domínio
- [ ] Guardas de estado e de saída no caminho do turno; LLM não cria o fato oficial
- [ ] Falha/ausência de LLM persiste turno pendente; nenhum fallback de formulário avança estado
- [ ] `active("guardrails")` e `active("reflection")` sensibilizados; vazio = no-op; reflection nunca substitui a saída
- [ ] `config.py` com protocol + provider + model_name por node; catálogo de providers na infra; adapter sem `getenv`
- [ ] Um adapter da porta (`in-process` ou `langgraph`); SDK LangGraph só em `adapters/langgraph/`
- [ ] Testes de nascimento verdes (slots, `active`, bloqueio, abertura, recap, `get` desconhecido, cancel, replay/`prefix`, MCP 401/perfil se houver `/mcp`, composição, config LLM)
- [ ] Guardas críticas têm matriz adversarial + teste de mutação; capacidades anunciadas possuem adapter e caminho e2e ativos
- [ ] Título de conversa (se houver lista): use case após a 1ª resposta, ≤6 palavras
- [ ] Roteamento determinístico vs modelo explícito; opção “parecida” não vira clique
- [ ] Checkpointer do runtime ≠ SSOT (banco do serviço)
- [ ] HITL: extract só `fields`; próxima pergunta do `ask_*` da lacuna; fake com `reply: Qual é a cidade?` não vaza para o outbound

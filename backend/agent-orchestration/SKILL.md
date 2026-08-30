---
name: agent-orchestration
description: >
  Use when creating, scaffolding, or birthing a product agent, changing
  ConversationalSpec, GraphSpec, WorkflowSpec, conversational vs operational
  flow, conversational/engine, specs/<job>, graph.py, config.py, prompts
  folder, prompts/guardrails.md, prompts/reflection.md, canonical copy vs
  prompt, LLM-driven turn, specialist/sub-agent, agent config.py,
  LLM_API_KEY, LLM_BASE_URL, getenv, guards, guardrails, output guard,
  state guard, or reflection. Activating Make/LangGraph/in-process:
  orchestration-runtime. LangGraph mention: langgraph-agents.
---

# Orquestração de agentes

O fluxo é **declarativo e neutro** (`ConversationalSpec` / `GraphSpec` / `WorkflowSpec`). O motor conversacional **recebe** o spec; o job concreto vive em `specs/<job>/`. Make.com, LangGraph ou outro runtime **compilam** o spec no adapter. O domínio não importa SDK de Make nem `StateGraph`.

Como o runtime de processo é escolhido e ligado no startup: skill `orchestration-runtime`. A pasta do spec é a mesma, qualquer que seja o adapter.

**REQUIRED BACKGROUND:** `AGENTS.md` hexagonal + `persistence-ports`. Banco e LLM são portas.

Nascer um agente — neste produto ou em qualquer outro — é a **receita abaixo**, no mesmo commit. Pular um passo = o agente **não nasceu**. Não existe “ligo a guarda depois” nem “reflection numa fase 2”.

## Um agente no primeiro lançamento

Comece com **um** agente conversacional, identificado pela capacidade (`conversational.<job>`). Ele conduz a jornada, confirma e publica o fato. Não existe `conversational/general` + `specialists/support` para o mesmo trabalho.

| Tentação | Por que não |
|----------|-------------|
| `general` roteando para `support` | um só trabalho cognitivo. “Agente geral para tudo” infla prompt, tools e risco |
| `specialist/support` como primeiro agente | specialist = pipeline operacional (documento, lote, job), não conversa. Escala humana **não** é outro LLM |
| Agente de escalonamento | HITL na **mesma** conversa ou fila de operação depois do fato de negócio. Determinístico |

Escalonar para humano: `PendingInteraction` / atribuição de operador, não um segundo manifest. Depois do fato oficial: fila institucional, não agente.

Segundo agente só com bounded context próprio (ex.: copiloto autenticado interno) + ADR + porta de invocação com allowlist. Sem pasta `specialists/` vazia.

## Receita de nascimento

Mesmo commit. Ordem abaixo. Conferência vazia = não pronto.

1. **Identidade.** `conversational.<job>` (v1: exatamente um) + pasta `specs/<job>/`. Operacional: bounded context + ADR. `AgentRegistry.explicit`. Sem auto-discovery. Manifest conversacional nasce com `requires_output_guard` (ou equivalente); `False` não registra.
2. **Slots de prompt.** Em `specs/<job>/prompts/`: `guardrails.md` e `reflection.md` (H1 mínimo). Conversacional: `understand_turn.md` + `ask_*.md` por fase. Catálogo **não carrega** se faltar `guardrails` ou `reflection`. O catálogo **não** tem pasta default de um job — `register.py` passa o diretório.
3. **Duas casas.** Semântica nos `.md`. Legal / recusa / recap no domínio. Schema/enum no domínio. `PromptCatalog` é porta; core não lê disco; versão no trace.
4. **Guardas no caminho.** Estado (schema) + `inspect_outbound` / `approve_outbound` no texto **gerado**. Recusa canônica no domínio. Sem a chamada de saída, o agente não ativa.
5. **Sensibilizar.** A jornada chama `active("guardrails")` e `active("reflection")`. Vazio = no-op. Ausente = não sobe. Reflection nunca substitui a saída; revisão **reentra** em `inspect_outbound`.
6. **Config de LLM.** `specs/<job>/config.py` é SSOT por node (`llm_turn`, `reflection` se o slot tiver corpo): modelo, provider, temperatura, max_tokens. Sem `getenv`, sem segredo, sem marca do produto. Segredo e URL vivem em settings do composition root, com nome de **capacidade** (`LLM_API_KEY` / `LLM_BASE_URL`) ou o nome padrão do provider (`OPENAI_API_KEY`). Adapter recebe a conexão injetada — `os.environ` no adapter é defeito. Sem provider escolhido: não invente `model_name` e **não** construa o adapter.
7. **Runtime.** Um adapter (`orchestration-runtime`). Capabilities exigidas ⊂ oferecidas. Mesmo builder na API e no worker.
8. **Testes de nascimento** (senão é teatro): catálogo falha sem cada slot; heading-only → `active` é `None`; bloqueia reivindicação e permite abertura canônica; recap intacto **e** montado das labels do spec; registro rejeita segundo agente no v1 e rejeita conversacional sem guarda de saída; engine não importa spec concreto nem copy canônica; composição: `execute_turn` chama a guarda no gerado; `config.py` existe no spec; adapter de LLM sem `getenv` e sem prefixo da marca.

Não abra PR / não declare pronto com item da conferência vazio.

## Dois gêneros (quando houver o segundo caso)

| | Conversacional | Operacional |
|--|----------------|-------------|
| Turnos | vários, pausa/retoma, HITL | pipeline com início e fim |
| Estado | sessão + histórico | documento / lote / job |
| LLM | conduz a conversa | um node; o resto determinístico |
| Exemplo de pasta | `specs/intake/` | `specs/document_extract/` |

Não invente árvore `specialists/` só para ter “cara de multi-agent”. O segundo conversacional é **outra pasta em `specs/`** + ADR, não um specialist vazio.

## Motor + specs (indústria)

Dois papéis, duas pastas. O motor **não** conhece o job. O job **não** reimplementa o motor. Prompts soltos na raiz do serviço = o segundo spec copia o primeiro.

```
agents/
  conversational/            # motor; recebe ConversationalSpec
    engine.py
  specs/
    <job>/                   # um job = uma pasta
      spec.py                # ConversationalSpec: fases, tokens, labels de recap, copy
      config.py              # SSOT de LLM por node — sem getenv
      register.py            # composition: build_catalog() + exporta SPEC
      prompts/
        guardrails.md        # slot sempre (passo 2)
        reflection.md        # slot sempre (passo 2)
        understand_turn.md
        ask_*.md
  core/domain/spec.py        # tipos: AgentManifest, CollectField, ConversationalSpec
```

In-process hexagonal (primeiro lançamento): esta árvore **é** o spec. Arquivo só existe quando **tem corpo que corre**. `graph.py`, `nodes/`, `edge.py`, `specialists/`, porta de fala, `presentation/http.py` sem consumidor = código morto.

`ConversationalEngine` interpreta o spec (entrada, coleta, recap, confirmação). Labels de recap, tokens, opening e completed **vivem no spec**. O engine não importa `canonical_texts` nem `specs.<job>`.

`tools/` do grafo **não** entram em `tools/list` do MCP. Publicar capacidade ou jornada: skill `mcp-tools`.

Quem **liga o processo** (in-process / Make / LangGraph) é `orchestration-runtime`. O motor conversacional é outra camada: interpreta o spec no turno.

### Node e edge (vocabulário da indústria)

Grafo (LangGraph, StateGraph, cenário Make): **node** = unidade de trabalho; **edge** = transição. Isso é o padrão. **Não** se materializa como `node.py` / `edge.py` vazios dentro do agente.

No in-process conversacional o spec **é** o grafo, em dados:

| Grafo | Onde vive agora |
|-------|-----------------|
| node (passo) | `CollectField`, `entry`, `confirm_step` |
| edge linear | `next_step`, `first_ask` |
| edge condicional | `continue_token`, `confirm_token`, `commands` |
| `graph.py` | `specs/<job>/spec.py` |
| checkpointer | `ConversationStore` (banco do serviço) |
| interrupt / HITL | atribuição de operador / status `human_pending` |

Quando um runtime **compilador** for o escolhido (ADR, **um** adapter — skill `orchestration-runtime`):

```
specs/<job>/
  spec.py       # continua o dono do job
  graph.py      # monta GraphSpec (NodeSpec + EdgeSpec) SEM SDK
  nodes/        # só funções de node que existem (LLM, tool, determinístico)
  prompts/      # inalterado
```

`GraphSpec` / `NodeSpec` / `EdgeSpec` são tipos de domínio. `edge.py` só se houver router real. O adapter (`infrastructure/adapters/langgraph/`) faz `GraphSpec → StateGraph`. `from langgraph.graph import StateGraph` no spec, no engine ou no use case é defeito. Ponte: `langgraph-agents`.

Não crie `nodes/` / `graph.py` / `edge.py` “para quando o LangGraph chegar”. O compilador nasce com o adapter.

### Acrescentar um spec

v1 registra exatamente um. A árvore já admite o segundo; o registro é que trava.

1. Pasta `specs/<job>/` com a receita de nascimento (slots, config, register).
2. ADR se for o **segundo** conversacional (bounded context próprio).
3. Append na tuple de `AgentRegistry.explicit`.
4. Composition escolhe o spec. Sem auto-discovery.
5. O motor já existe — **não** copie `engine.py`.

### Um runtime, um canal — não throwaway

LangGraph **agora** para “depois trocar por Make” = dois adapters descartáveis. Escolha **um** (`orchestration-runtime`) e compile o spec nele. In-process já orquestra o grafo de coleta. LangGraph entra quando a ADR o escolhe como **o** runtime — não como ensaio.

Canal de entrada: o provider do requisito do v1 (API oficial, template pré-aprovado, identidade, janela de envio). Cliente não oficial da sessão web do canal (Evolution, Baileys e equivalentes) **não** é stepping stone: identidade, webhook e template não sobrevivem à troca. Dev local sem credencial: adapter fake ou sandbox **atrás da mesma porta** do messaging-gateway.

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

**Roteamento do turno (determinístico):** escolha explícita que casa **exato** com uma opção oferecida → sem modelo; o valor entra no estado. Todo o resto (livre, áudio/transcrição, correção, ambiguidade, fora de ordem, “parecido”) → turno de modelo. Classificar mal é defeito bloqueante. Clicar é otimização de custo, não restrição.

Turno de modelo:

1. `active("guardrails")` (se houver) + prompt da tarefa + versão no trace
2. `LlmPort` propõe patch tipado + evidência no histórico
3. Guarda de **estado** aceita ou rejeita o patch
4. Se gerado e `active("reflection")`: passe de qualidade; revisão volta ao texto
5. Guarda de **saída** **sempre** no texto a entregar (depois da reflection)
6. Canônico, recap e eco de valor já confirmado **não** passam por geração, reflection nem guarda de geração — só se despacham

`PromptCatalog` é porta. Os `.md` carregam-se no composition root / adapter de arquivos. Domínio não lê disco. Versão (hash ou tag) registra-se em cada `AgentRun`. Sem I/O no `core/`.

Não coloque enum de categoria ou regra de confirmação no prompt. Política de nunca-prometer mora em `prompts/guardrails.md`; o matcher 100% mora em `inspect_outbound`. Não coloque “como perguntar a regional em linguagem natural” em constante Python.

## Config de LLM — três casas

Marca do produto no nome da variável (`ACME_LLM_TOKEN`) acopla o código ao tenant. Adapter que lê `os.environ` fura o composition root. `config.py` com a chave da API mistura segredo com política do node.

| Casa | Mora | Não mora |
|------|------|----------|
| `specs/<job>/config.py` | modelo, provider, temperatura, max_tokens **por node** | `getenv`, URL, token, prefixo da marca |
| Settings (composition root) | conexão: `LLM_API_KEY` / `LLM_BASE_URL` **ou** o nome padrão do provider | qual node usa qual modelo |
| Adapter (`LlmPort`) | HTTP/SDK com URL e token **injetados** | `os.environ`, fallback silencioso (`complete` vazio se faltar URL) |

`LlmNodeConfig` é value object de domínio (dataclass fria). Sem Pydantic no core. Sem `api_key` no config do node — o DI passa a conexão.

```
NODE_CONFIGS = {
    "llm_turn": LlmNodeConfig(temperature=0.2, max_tokens=4096, model_name=..., provider=...),
    "reflection": LlmNodeConfig(temperature=0.2, max_tokens=2048, model_name=..., provider=...),
}
```

Não declare node LLM chamado `guardrails`: a guarda de saída é determinística. Juiz-LLM, se existir, é rede extra **depois** de `inspect_outbound`, com outro nome.

Env: capacidade ou contrato de mercado, nunca marca.

| Ok | Defeito |
|----|---------|
| `LLM_API_KEY`, `LLM_BASE_URL` | `TENDA_LLM_TOKEN`, `ACME_GPT_KEY` |
| `OPENAI_API_KEY` (se o provider for esse) | `PRODUTO_OPENAI_KEY` |

Sem provider escolhido, `model_name`/`provider` ficam `None` e o composition **não** instancia o adapter. Completar o config com um modelo inventado é teatro.

A mesma regra vale para **todo** env e **schema SQL**, não só LLM: constituição §3.1. `agents.conversations` atrás de `ConversationStore`. Não `workspace.conversations` nem `TENDA_PG_*`.

## Guardas — montagem e uso

Três peças. Não são sinônimos. Biblioteca `guardrails` (SDK) é **adapter opcional**, nunca o dono da regra.

| Peça | Faz | Não faz | Quem implementa |
|------|-----|---------|-----------------|
| Guarda de **estado** | aceita ou rejeita o patch no schema (campo, fase, confirmação, criação do fato) | redigir a resposta | domínio / application, 100% determinística |
| Guarda de **saída** | decide o que **pode ser entregue** ao humano | qualidade, tom, “atendeu o pedido” | application, 100% determinística **antes** de qualquer juiz-LLM |
| Reflection | qualidade: idioma, aderência, coerência | bloquear segurança; liberar o que a saída bloqueou | segundo passe se o slot tiver conteúdo |

Passos 2, 4 e 5 da receita: as duas guardas no caminho **e** os dois arquivos. Um só desenho de jornada. Sem o nó de saída **ou** sem qualquer um dos dois arquivos, o agente **não ativa**.

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

## Red flags

- SDK de runtime no `core/` / `application/` (ativação: `orchestration-runtime`)
- SQL no `graph.py`
- Dois agentes conversacionais para o mesmo usuário no primeiro lançamento
- Pasta `specialists/support` sem segundo domínio
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
- Inventar `graph.py` / `nodes/` / `edge.py` / `specialists/` no in-process só para cumprir a árvore
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
- `api_key` ou URL no `config.py` do agente
- Node LLM chamado `guardrails` no lugar de `inspect_outbound`
- `complete()` devolvendo vazio quando falta URL (fallback silencioso)

## Conferência

Antes de declarar pronto, copie e marque. Caixa vazia = o agente **não nasceu**.

- [ ] Identidade: um conversacional no v1 (ou operacional + ADR); pasta `specs/<job>/`; registro explícito; `requires_output_guard`
- [ ] Motor em `conversational/` recebe spec; engine sem import de job nem de copy canônica; sem `node.py`/`edge.py`/`graph.py` vazios
- [ ] Sem stub, porta ou presentation sem consumidor; sem segundo runtime/canal throwaway
- [ ] `specs/<job>/prompts/guardrails.md` e `reflection.md` no mesmo commit; catálogo falha sem qualquer um; catálogo sem pasta default de um job
- [ ] Duas casas: semântica nos `.md`; legal/recusa/recap e schema no domínio
- [ ] Guardas de estado e de saída no caminho do turno; LLM não cria o fato oficial
- [ ] `active("guardrails")` e `active("reflection")` sensibilizados; vazio = no-op; reflection nunca substitui a saída
- [ ] `config.py` SSOT por node; settings com nome de capacidade; adapter sem `getenv` e sem prefixo da marca
- [ ] Runtime: um adapter (`orchestration-runtime`); capabilities no startup; mesmo builder API/worker
- [ ] Testes de nascimento verdes (slots, `active`, bloqueio, abertura, recap, registro, composição, config LLM)
- [ ] Título de conversa (se houver lista): use case após a 1ª resposta, ≤6 palavras
- [ ] Roteamento determinístico vs modelo explícito; opção “parecida” não vira clique
- [ ] Checkpointer do runtime ≠ SSOT (banco do serviço)

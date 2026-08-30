---
name: agent-orchestration
description: >
  Use when creating or changing a product agent, GraphSpec, WorkflowSpec,
  conversational vs operational flow, graph.py, config.py, prompts folder,
  prompts/guardrails.md, prompts/reflection.md, canonical copy vs prompt,
  LLM-driven turn, specialist/sub-agent, agent guards, guardrails, output
  guard, state guard, or reflection. Activating Make/LangGraph/in-process:
  orchestration-runtime. LangGraph mention: langgraph-agents.
---

# Orquestração de agentes

O fluxo é **declarativo e neutro** (`GraphSpec` / `WorkflowSpec`). Make.com, LangGraph ou outro runtime **compilam** isso no adapter. O domínio não importa SDK de Make nem `StateGraph`.

Como o motor é escolhido e ligado no startup: skill `orchestration-runtime`. A pasta do agente é a mesma, qualquer que seja o adapter.

**REQUIRED BACKGROUND:** `AGENTS.md` hexagonal + `persistence-ports`. Banco e LLM são portas.

## Um agente no primeiro lançamento

Comece com **um** agente conversacional, identificado pela capacidade (`conversational.<job>`). Ele conduz a jornada, confirma e publica o fato. Não existe `conversational/general` + `specialists/support` para o mesmo trabalho.

| Tentação | Por que não |
|----------|-------------|
| `general` roteando para `support` | um só trabalho cognitivo. “Agente geral para tudo” infla prompt, tools e risco |
| `specialist/support` como primeiro agente | specialist = pipeline operacional (documento, lote, job), não conversa. Escala humana **não** é outro LLM |
| Agente de escalonamento | HITL na **mesma** conversa ou fila de operação depois do fato de negócio. Determinístico |

Escalonar para humano: `PendingInteraction` / atribuição de operador, não um segundo manifest. Depois do fato oficial: fila institucional, não agente.

Segundo agente só com bounded context próprio (ex.: copiloto autenticado interno) + ADR + porta de invocação com allowlist. Sem pasta `specialists/` vazia.

## Dois gêneros (quando houver o segundo caso)

| | Conversacional | Operacional |
|--|----------------|-------------|
| Turnos | vários, pausa/retoma, HITL | pipeline com início e fim |
| Estado | sessão + histórico | documento / lote / job |
| LLM | conduz a conversa | um node; o resto determinístico |
| Exemplo de pasta | `agents/intake/` | `agents/document_extract/` |

Não invente árvore `specialists/` só para ter “cara de multi-agent”.

## Pasta de um agente (agnóstica)

```
<agente>/
  config.py       # modelo/temperatura por node — SSOT; sem SDK de runtime
  graph.py        # monta GraphSpec/WorkflowSpec; injeta ports
  state.py
  register.py     # composition; recebe OrchestrationRuntimePort, LLM, repos
  prompts/
    guardrails.md      # slot sempre: política ao modelo
    reflection.md      # slot sempre: qualidade; nunca segurança
    understand_turn.md # conversacional: como compreender o turno
    ask_*.md           # próxima lacuna (por fase)
  nodes/          # só pipeline operacional
  tools/          # internas do grafo: schema, timeout, idempotency, allowlist
```

`tools/` do grafo **não** entram em `tools/list` do MCP. Publicar capacidade ou jornada: skill `mcp-tools`.

`register.py` devolve o spec. Quem **compila e executa** o turno é `orchestration-runtime` (um adapter, capabilities no startup, mesmo builder na API e no worker).

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

## Guardas — montagem e uso

Três peças. Não são sinônimos. Biblioteca `guardrails` (SDK) é **adapter opcional**, nunca o dono da regra.

| Peça | Faz | Não faz | Quem implementa |
|------|-----|---------|-----------------|
| Guarda de **estado** | aceita ou rejeita o patch no schema (campo, fase, confirmação, criação do fato) | redigir a resposta | domínio / application, 100% determinística |
| Guarda de **saída** | decide o que **pode ser entregue** ao humano | qualidade, tom, “atendeu o pedido” | application, 100% determinística **antes** de qualquer juiz-LLM |
| Reflection | qualidade: idioma, aderência, coerência | bloquear segurança; liberar o que a saída bloqueou | segundo passe se o slot tiver conteúdo |

Agente **nasce** com as duas guardas no caminho do turno **e** com `prompts/guardrails.md` + `prompts/reflection.md`. Um só desenho de jornada. Manifest/registro declara a guarda de saída (`requires_output_guard` / equivalente). Sem o nó **ou** sem qualquer um dos dois arquivos, o agente **não ativa**.

### Slots sempre ligados

Os dois arquivos existem desde o primeiro commit. A jornada os sensibiliza sempre. Não há grafo “com reflection” e grafo “sem”.

| Slot | Arquivo vazio (só H1/branco) | Com conteúdo | Nunca |
|------|------------------------------|--------------|-------|
| `guardrails.md` | não prefixa o modelo | prefixa política | **não** desliga `inspect_outbound` |
| `reflection.md` | não há segundo passe | qualidade | **não** bloqueia segurança; **não** libera bloqueio da saída |

Arquivo **ausente** ≠ arquivo **vazio**. Ausente é defeito (slot apagado; catálogo não carrega). Vazio é escolha (ainda não preencheu; no-op).

Jornada usa `catalog.active(nome)` → texto ou `None` (sem corpo além de título). `get` só prova que o arquivo existe. Concatenar `get` de slot vazio injeta um H1 inútil.

### Como criar

No mesmo commit que o agente, criar os dois arquivos (podem nascer só com o H1):

1. `prompts/guardrails.md` — política ao modelo; quatro seções se houver conteúdo
2. `prompts/reflection.md` — qualidade; seções idioma / aderência / coerência se houver conteúdo
3. Catálogo falha fechado se faltar `guardrails` **ou** `reflection`
4. `active("guardrails")` prefixa o turno de modelo **só** se houver corpo
5. `active("reflection")` dispara o passe de qualidade **só** se houver corpo; revisão, se houver, **reentra** em `inspect_outbound`
6. Matchers 100% em `inspect_outbound` (independente do md estar vazio). Recusa canônica no domínio — nenhum dos dois arquivos a redige

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
- Agente conversacional registrado sem guarda de saída no caminho do turno
- Agente sem `prompts/guardrails.md` ou sem `prompts/reflection.md`
- Dois grafos (com/sem reflection) em vez de slot vazio
- Política de nunca-prometer só em `understand_turn.md`
- `guardrails.md` vazio usado para pular `inspect_outbound`
- `get("reflection")` concatenado sem `active` (injeta H1 vazio)
- `guardrails.md` como única enforcement (sem `inspect_outbound`)

## Conferência

Antes de declarar pronto, copie e marque. Caixa vazia = falta.

- [ ] Spec neutro (`GraphSpec`/`WorkflowSpec`); motor em `orchestration-runtime`
- [ ] Um agente conversacional no primeiro lançamento, se for o caso
- [ ] Registro explícito no startup; sem auto-discovery
- [ ] Título de conversa (se houver lista): use case após a 1ª resposta, ≤6 palavras
- [ ] Guardas de estado e de saída determinísticas no caminho do turno; LLM não cria o fato oficial
- [ ] `prompts/guardrails.md` e `prompts/reflection.md` existem; catálogo falha sem qualquer um; `active` no-op se vazio; reflection nunca substitui a guarda de saída
- [ ] Saída: recusa canônica; recap/legal intactos; sem retry que contorna; testes de bloqueio e de permissão
- [ ] Turno de modelo usa `prompts/*.md` versionados; cópia legal/recap/recusa fica canônica no domínio
- [ ] Roteamento determinístico vs modelo explícito; opção “parecida” não vira clique
- [ ] Checkpointer do runtime ≠ SSOT (banco do serviço)

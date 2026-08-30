---
name: agent-orchestration
description: >
  Use when creating or changing a product agent, GraphSpec, WorkflowSpec,
  conversational vs operational flow, graph.py, config.py, prompts folder,
  canonical copy vs prompt, LLM-driven turn, specialist/sub-agent, or agent
  guards. Activating Make/LangGraph/in-process: orchestration-runtime.
  LangGraph mention: langgraph-agents.
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
  prompts/        # .md versionados; versão no trace
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

1. `PromptCatalog.get(...)` + versão no trace
2. `LlmPort` propõe patch tipado + evidência no histórico
3. Guarda de **estado** aceita ou rejeita o patch
4. Texto ao colaborador: modelo **ou** canônico; guarda de **saída** no gerado
5. Canônico, recap e eco de valor já confirmado **não** passam pela guarda de geração — só se despacham

`PromptCatalog` é porta. Os `.md` carregam-se no composition root / adapter de arquivos. Domínio não lê disco. Versão (hash ou tag) registra-se em cada `AgentRun`. Sem I/O no `core/`.

Não coloque enum de categoria, regra de confirmação ou “prometa sigilo” no prompt. Não coloque “como perguntar a regional em linguagem natural” em constante Python.

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

## Conferência

Antes de declarar pronto, copie e marque. Caixa vazia = falta.

- [ ] Spec neutro (`GraphSpec`/`WorkflowSpec`); motor em `orchestration-runtime`
- [ ] Um agente conversacional no primeiro lançamento, se for o caso
- [ ] Registro explícito no startup; sem auto-discovery
- [ ] Título de conversa (se houver lista): use case após a 1ª resposta, ≤6 palavras
- [ ] Guardas de estado e de saída determinísticas; LLM não cria o fato oficial
- [ ] Turno de modelo usa `prompts/*.md` versionados; cópia legal/recap/recusa fica canônica no domínio
- [ ] Roteamento determinístico vs modelo explícito; opção “parecida” não vira clique
- [ ] Checkpointer do runtime ≠ SSOT (banco do serviço)

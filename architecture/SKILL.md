---
name: architecture
description: >
  Use when designing a system, choosing bounded contexts, drawing module
  boundaries, writing an ADR, or deciding where a capability lives. Also
  when the user mentions architecture, hexagonal layout, or /architecture.
  After implementation, run principles-audit and security-audit until zero
  findings. Worktree, branch and PR: git-activity.
---

# Arquitetura

**REQUIRED BACKGROUND:** constituição `AGENTS.md` (princípios, hexagonal, dimensões §5). Esta skill é o **desenho** e o **gate de entrega**. Skills de pasta (`http-apis`, `auth`, `agent-orchestration`, `frontend-surfaces`, `cicd`, …) executam o recorte. Abrir worktree/PR: `git-activity`. Defeito: `debug-hypotheses`. Harness de cliente: `client-harness`.

## Como desenhar

1. **Invariante primeiro.** O que não pode quebrar? Sem isso, não há desenho.
2. **Dono do dado.** Um bounded context escreve; o resto consome contrato (HTTP/evento). Sem tabela compartilhada.
3. **Camada.** presentation → application → core ← infrastructure. SDK e framework só no adapter.
4. **Porta pequena.** Runtime de agente, IdP, banco, fila, LLM: um porto por capacidade.
5. **Uma abordagem.** Plano em `docs/plans/<slug>.md` se não for trivial. ADR só para decisão que sobrevive ao PR. Pedido que empacota vários módulos independentes: **capability map** (id, responsabilidade, depende-de, ordem de build) **antes** de cada plano — o humano revisa o mapa.

6. **YAGNI de serviço.** Worker no mesmo deployável antes de microsserviço. Segundo agente só com segundo domínio.
7. **Fatia vertical.** Um caminho ponta a ponta (teste → dono → superfície), depois o próximo. Sem commit automático — `git-discipline`.

## Completude vertical antes do primeiro teste

Para cada requisito tocado, registre no plano (ou na análise do diff trivial) uma linha com:

```
requisito/fonte → entrada autorizada → principal/tenant → use case → dono do dado
→ saída autorizada → falhas/retry/concorrência → testes negativos e de retomada
```

Não é documentação paralela: é a prova de que o comportamento chega ao dono e volta pela
superfície correta. Campo coletado e descartado, capacidade anunciada sem adapter ativo,
rota sem consumidor aprovado e teste que valida comportamento contrário ao requisito são
falhas de completude, mesmo com cobertura alta.

Selecione as skills pelo que o recorte **contém**, não só pelo pedido original.
**Kit (uma tabela):** Gate 2 de `analyze-before-implement`. Se o diff tiver sinal que o pedido não citou, acrescente essa linha do kit e marque a conferência dela. Não copie a tabela para cá.

Vista mental (indústria, sem diagrama obrigatório): contexto → limites (containers) → módulos (hexagonais) → adapters. Não comece pelo controller nem pela tela.

**Entrada hostil tem teto.** Campo escrito por humano — login, busca, catálogo, contato, compositor — nasce com limite. `maxLength` na UI **não** autoriza: o schema HTTP (`Field(max_length=)` / `Query(max_length=)`) é o gate. Os números são os mesmos nas duas pontas (teste de architecture). Sem teto = achado. Download em massa e ação irreversível pedem confirmação (modal), não clique único.

Pacote `packages/platform` (no monorepo com UI: `backend/packages/platform`): mecânica **sem domínio**. Porto + Memory fake + adapter do provider. **SRP: uma pasta por capacidade**, nunca `.py` solto na raiz (só `__init__.py`):

```
platform/
  cache/      port, memory, redis
  events/     port, envelope, memory, rabbit|streams, retry
  inbox/      port, memory
  postgres/   connection (pool + SET tenant)
  logs/       redact, json
```

**Não** mora aí: `INSERT INTO <bc>.…`, fábrica de evento de um produtor (`order.created`, `message.received`), SQL de inbox do dono da tabela. Adapter Postgres da inbox fica no bounded context que **possui** a tabela. Fábrica do fato fica no serviço produtor. Contrato do tipo de evento, se compartilhado, fica em `packages/contracts`. Arquivo na raiz do pacote = achado de SRP.

## Onde mora cada coisa

| Capacidade | Skill |
|------------|-------|
| API HTTP | `http-apis` |
| Identidade | `auth` |
| MCP (servidor / transporte) | `mcp-servers` |
| MCP (tool / jornada / perfil) | `mcp-tools` |
| Agente (motor conversacional, specs/<job>, NodeType, contratos de ANALYSIS) | `agent-orchestration` |
| Runtime de orquestração (ativação) | `orchestration-runtime` |
| Persistência | `persistence-ports` + `sql-migrations` + `sql-dialects` |
| Eventos / outbox | `reliable-messaging` |
| Cache | `cache-ports` |
| Object storage | `object-storage` |
| Logs / traces / métricas | `observability` |
| Canal WhatsApp (Evolution, Twilio, …) | `whatsapp-channel` |
| Worker / job | `background-workers` |
| Área pública / tema / i18n / viewport | `frontend-surfaces` |
| Login | `frontend-login` |
| Área logada | `frontend-shell` |
| Chat | `frontend-chat` |
| Fila operacional / tickets | `ops-backoffice` |
| UI do backoffice | `frontend-backoffice` |
| CI/CD, gates, workflows | `cicd` |

## Gate depois de implementar

Não declare pronto no `make test` verde.

**Review do diff (não é o audit).** Cinco eixos no recorte: correção, leitura, encaixe hexagonal, segurança, desempenho. Sem inventário do repo. Repo inteiro + PDF: `principles-audit` / `security-audit`. Simplificar só com testes verdes e comportamento idêntico (cerca de Chesterton: não apague o que não entende).

**Fan-out.** Dispare os dois audits **no mesmo turno, em paralelo**. O agente principal sintetiza:

```
Ship: GO | NO-GO
Blockers (must): …
Rollback: gatilho · procedimento · RTO
```

Crítico num audit → default NO-GO até o humano aceitar o risco. Rollback escrito **antes** de GO. Pular o fan-out só se as três forem verdade: ≤2 arquivos, <50 linhas, e o diff **não** toca auth, pagamento, dado ou config/env.

**Performance.** Sem número, não otimize. Medir → gargalo → corrigir → medir → guardar regressão. Telemetria: `observability`.

**Decisão não trivial** (auth, contrato publicado, migração irreversível): no chat, CLAIM + artefato; revisor em contexto fresco viesado a **desprovar**. Sessão principal; persona não despacha persona.

Loop **obrigatório**:

0. Reexecutar a completude vertical e as conferências de **todas** as capacidades detectadas.
1. Rodar os gates canônicos reais (`make lint typecheck test check-architecture check-migrations build`) e validar o manifesto de deploy (`docker compose config`, quando houver).
2. Fan-out `/principles-audit` + `/security-audit` no diff.
3. Cada achado: corrige no dono do fato (não no relatório).
4. Roda gates e **os dois** audits de novo.
5. Entrega só com **GO**, zero achados e zero gate vermelho. “É frontend” / “é skill” / “é migração” não isenta.

Sem `|| true`, sem achar ignorado por nome. Exceção só por ADR com prazo.

## Quando não usar

- Diff de produto para varrer: `principles-audit` / `security-audit`.
- Worktree, branch, PR: `git-activity`.
- Defeito com sintoma: `debug-hypotheses` antes de redesenhar.

## Desculpas que não valem

| Desculpa | Realidade |
|----------|-----------|
| É óbvio, pulo o plano | Sem invariante, não há desenho. `docs/plans/` existe para isso. |
| Depois eu meço performance | Dimensão 9 é o mesmo diff. Medir primeiro; não adivinhar. |
| Os audits eu corro no fim se sobrar tempo | Gate de entrega: fan-out agora, não “depois”. |

## Red flags

- Pasta por entidade (`/users`, `/orders`) como “serviço”
- Segundo runtime ou segundo agente sem capability matrix / ADR
- Começar pelo provider (Make, LangGraph, Auth SaaS) e encaixar o domínio depois
- Runtime ou canal throwaway (“LangGraph agora, Make depois”; “Evolution agora, provider oficial depois”)
- Porta/stub/`node.py` sem caminho de execução
- Grafo com nó ANALYSIS sem tipo de saída em `schemas.py` (JSON/`dict` no use case)
- Pular o loop de auditoria
- Declarar capacidade na UI/contrato sem caminho ativo até o adapter e teste de ponta a ponta
- Marcar rota pública como intencional sem requisito/ADR aceito que autorize a superfície
- SQL ou evento de um bounded context no pacote de plataforma
- `logs.py` / `postgres.py` / `ports.py` na raiz do pacote de plataforma (a capacidade é pasta)
- `reject(requeue=True)` como se incrementasse `x-death` (não incrementa; teto de retry nunca dispara)
- Input/textarea sem `maxLength` ou schema HTTP sem `max_length` (teto só no cliente não conta)
- Download em massa ou exclusão no primeiro clique, sem confirmação

## Conferência

Antes de declarar pronto, copie e marque. Caixa vazia = falta.

- [ ] Invariante e dono do dado escritos
- [ ] Completude vertical dos requisitos tocados; nenhum campo/capacidade/rota termina sem dono e consumidor
- [ ] Camada certa; porto pequeno; composition root único
- [ ] Pacote de plataforma: pasta por capacidade; raiz só `__init__.py`; sem SQL/fábrica de BC
- [ ] Skill do recorte lida e conferência dela marcada
- [ ] Skills adicionais selecionadas pelas capacidades presentes no diff
- [ ] Sem microsserviço/segundo agente sem o critério da constituição
- [ ] Gates canônicos + manifesto de deploy verdes; fan-out dos dois audits em zero achados; rollback escrito se o recorte foi a produção
- [ ] Campos escritos por humano com teto iguais na UI e no schema HTTP
- [ ] Sem otimização sem medição; decisão não trivial cruzada se o recorte era auth/contrato/migração

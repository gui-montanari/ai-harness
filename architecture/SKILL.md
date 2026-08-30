---
name: architecture
description: >
  Use when designing a system, choosing bounded contexts, drawing module
  boundaries, writing an ADR, starting a feature, or deciding where a
  capability lives. Also when the user mentions architecture, hexagonal
  layout, or /architecture. After implementation, run principles-audit and
  security-audit until zero findings.
---

# Arquitetura

**REQUIRED BACKGROUND:** constituição `AGENTS.md` (princípios, hexagonal, dimensões §5). Esta skill é o **desenho** e o **gate de entrega**. Skills de pasta (`http-apis`, `auth`, `agent-orchestration`, `frontend-surfaces`, …) executam o recorte.

## Como desenhar

1. **Invariante primeiro.** O que não pode quebrar? Sem isso, não há desenho.
2. **Dono do dado.** Um bounded context escreve; o resto consome contrato (HTTP/evento). Sem tabela compartilhada.
3. **Camada.** presentation → application → core ← infrastructure. SDK e framework só no adapter.
4. **Porta pequena.** Runtime de agente, IdP, banco, fila, LLM: um porto por capacidade.
5. **Uma abordagem.** Plano em `docs/plans/<slug>.md` se não for trivial. ADR só para decisão que sobrevive ao PR.
6. **YAGNI de serviço.** Worker no mesmo deployável antes de microsserviço. Segundo agente só com segundo domínio.

Vista mental (indústria, sem diagrama obrigatório): contexto → limites (containers) → módulos (hexagonais) → adapters. Não comece pelo controller nem pela tela.

## Onde mora cada coisa

| Capacidade | Skill |
|------------|-------|
| API HTTP | `http-apis` |
| Identidade | `auth` |
| MCP | `mcp-servers` |
| Agente / Make / LangGraph | `agent-orchestration` |
| Persistência | `persistence-ports` + `sql-migrations` + `sql-dialects` |
| Eventos / outbox | `reliable-messaging` |
| Worker / job | `background-workers` |
| Área pública / tema / i18n / viewport | `frontend-surfaces` |
| Login | `frontend-login` |
| Área logada | `frontend-shell` |
| Chat | `frontend-chat` |
| Fila operacional / tickets | `ops-backoffice` |
| UI do backoffice | `frontend-backoffice` |

## Gate depois de implementar

Não declare pronto no `make test` verde. Loop **obrigatório**:

0. Conferência da skill do recorte — caixas marcadas.
1. `/principles-audit` no diff.
2. `/security-audit` no diff.
3. Cada achado: corrige no dono do fato (não no relatório).
4. Roda **os dois** de novo.
5. Entrega só com **zero** achados. “É frontend” / “é skill” / “é migração” não isenta.

Sem `|| true`, sem achar ignorado por nome. Exceção só por ADR com prazo.

## Red flags

- Pasta por entidade (`/users`, `/orders`) como “serviço”
- Segundo runtime ou segundo agente sem capability matrix / ADR
- Começar pelo provider (Make, LangGraph, Auth SaaS) e encaixar o domínio depois
- Pular o loop de auditoria

## Conferência

Antes de declarar pronto, copie e marque. Caixa vazia = falta.

- [ ] Invariante e dono do dado escritos
- [ ] Camada certa; porto pequeno; composition root único
- [ ] Skill do recorte lida e conferência dela marcada
- [ ] Sem microsserviço/segundo agente sem o critério da constituição
- [ ] `/principles-audit` e `/security-audit` em zero achados

---
name: observability
description: >
  Use when adding logs, metrics, traces, correlation_id, redaction, health
  vs ready, dashboards, or when a handler would log a request body, token,
  or PII. OpenTelemetry is the default shape; vendor SDKs stay in adapters.
---

# Observabilidade

Rastrear o fluxo **sem** gravar o que não pode vazar. Padrão aberto (OpenTelemetry). Vendor (Datadog, Grafana Cloud, …) é adapter, não o domínio.

**REQUIRED BACKGROUND:** `AGENTS.md` observabilidade + §8.1 (PII). Health HTTP: `http-apis`.

## Antes de implementar — pergunte

Se o destino de telemetria **ainda não** está no ADR/`AGENTS.md`:

> Para onde vão traces/métricas neste produto?
> 1. OpenTelemetry Collector (OTLP)
> 2. Outro (nomeie o backend)
> 3. Só logs estruturados neste recorte

Implemente **um** exporter. Três vendors “por se acaso” é YAGNI. Logs estruturados existem sempre.

## O que todo request/worker carrega

`trace_id`, `correlation_id`, `causation_id`, `tenant_id` (opaco). Propagar em HTTP e no envelope de evento (`reliable-messaging`). Sem esses IDs o diagnóstico vira grep de PII.

## Logs

JSON, um evento por linha. Nível explícito. Mensagem **sem** relato, telefone, e-mail, token, cookie, Authorization, prompt completo, body cru.

Filtro de redação no handler de logging (bearer, JWT-like, `password=`). Filtro é defesa extra — o código **não** loga o campo.

Proibido: `logger.info(request.body)`, `print(token)`, exception com query string de segredo.

## Métricas e traces

- RED nas APIs (rate, error, duration). USE em worker/fila (utilização, saturacao, erros, profundidade, idade, DLQ).
- Domínio: contadores do fato (criado/concluído/abandonado), **não** o conteúdo.
- Label de métrica: tenant opaco no máximo. Sem `user_email`, sem protocolo humano se for enumerável.
- Span: nome da operação + ids opacos. Atributo não é dump do payload.
- Exporter OTLP no composition root. `core/` não importa SDK de vendor.

## Saúde

`/health` = processo vivo (liveness). `/ready` = pode receber carga (engine, fila). Liveness **não** pinga Redis/DB (blip mata o cluster). `http-apis`.

Auditoria de negócio (`ops-backoffice`) **não** é log técnico. São dois fluxos.

## Red flags

- PII ou token em log, trace, métrica, URL de erro
- SDK de APM em `core/` / `application/`
- Liveness acoplada ao Redis
- `console.log` do body no frontend autenticado
- Trace que guarda o prompt completo ou o relato

## Conferência

Antes de declarar pronto, copie e marque. Caixa vazia = falta.

- [ ] `trace_id` / `correlation_id` / `tenant_id` no request e no evento
- [ ] Log JSON; redação; zero PII/segredo no recorte
- [ ] Métricas sem label de pessoa; spans sem payload
- [ ] Exporter no composition root; um destino
- [ ] `/health` ≠ `/ready`; liveness sem dependência externa
- [ ] Auditoria de negócio não mistura com log técnico

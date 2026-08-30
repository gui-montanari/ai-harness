---
name: cache-ports
description: >
  Use when adding a cache, Redis GET/SET, TTL, cache-aside, stampede,
  tenant-scoped keys, or when a use case would import redis.asyncio for
  something that is not an event stream. Event bus: reliable-messaging.
---

# Cache por porta

Cache é **derivado**. O SSOT continua no banco/serviço dono. Miss reconstrói. TTL e invalidação são explícitos. O domínio não importa cliente Redis.

**REQUIRED BACKGROUND:** `AGENTS.md` §8.4. Streams/filas: `reliable-messaging` — **outro porto**, mesmo que o processo fale com o mesmo Redis.

## Antes de implementar — pergunte

Se o produto **ainda não** tem cache escolhido:

> Qual cache neste produto?
> 1. Redis (candidato conhecido)
> 2. Nenhum — não precisa neste recorte
> 3. Outro (nomeie)

Não invente cache “porque toda API tem”. Sem hot path medido ou requisito de TTL, a resposta correta pode ser **nenhum**. Se disserem Redis, implemente **só** Redis. Segundo provider só com segundo ambiente real.

## Porto

```
CachePort.get(key) -> bytes | None
CachePort.set(key, value, ttl)
CachePort.delete(key)
```

Opcional e pequeno: `get_many` / `delete_prefix` se houver segundo uso real. Não crie `CacheService` com get+set+lock+pubsub+stream.

Chave: `t:{tenant}:{namespace}:{id}`. Sem tenant na chave = vazamento. Serialização no adapter (JSON). Valor **sem** PII, segredo, token, relato.

TTL **obrigatório**. Sem TTL = cresce até matar o Redis. Invalidação no mesmo use case que grava o SSOT (delete da chave). Cache-aside: miss → origem → set.

## Redis (quando escolhido)

- **URL obrigatória**, injetada: `RedisCache(url, timeout=…)`. Adapter **recusa vazio** no construtor. `getenv` só na composition (`REDIS_URL`). Host `127.0.0.1` ≠ DNS do compose (`redis`); o yaml do container **não** reusa o URL do `.env` do host.
- Cliente **async**, pool com teto, timeout, retry só em timeout/conexão (política global).
- Factory no composition root. API e worker **herdam** o mesmo client (ou o mesmo builder).
- No monorepo: porto + Memory + Redis em `packages/platform/cache/` (pasta da capacidade; nada na raiz). Use case não importa `redis`.
- Standalone vs cluster pela config — não os dois no código do use case.
- Prefixo de ambiente na chave (`env:`) para não colidir dev/prod no mesmo cluster.
- Não use `KEYS *`. `SCAN` ou chave conhecida.
- Stampede: um lock curto por chave no miss concorrente, ou aceite N rebuilds com TTL baixo. Sem `SETNX` copiado em 12 repositórios — um helper no adapter.
- Queda do Redis: o produto **continua** (miss → origem). 5xx do cache não vira 500 se a origem responde. Stale-on-error (fresh TTL curto + stale TTL longo) só com segundo caso concreto.
- Liveness **não** pinga o Redis (blip derrubaria o cluster). Readiness pode.

Streams (`XADD`) **não** passam por este porto. Pub/sub de SSE, se existir, é adapter de transporte, não `CachePort`.

`MemoryCache` no teste de use case (dict + TTL pelo `Clock`). Contract test contra Redis em container.

## Red flags

- `redis.get` no use case / handler / grafo
- Cache como única cópia do dado
- Chave sem `tenant_id`; valor com PII
- Sem TTL; `FLUSHALL` no código de produto
- Um `RedisService` que faz cache **e** stream **e** lock
- Três clientes Redis no mesmo processo com configs diferentes
- Liveness dependente do Redis
- Adapter Redis lendo `os.environ`; URL vazia que sobe “sem cache” em silêncio
- `REDIS_URL` do host interpolado no compose (hostname errado dentro do container)

## Conferência

Antes de declarar pronto, copie e marque. Caixa vazia = falta.

- [ ] Precisa de cache de verdade (ou a resposta foi “nenhum”)
- [ ] Provider perguntado; **um** adapter
- [ ] `CachePort` no core/platform; Redis só no adapter; URL injetada e fail-closed; I/O async
- [ ] Chave com tenant + namespace; TTL; invalidação no writer
- [ ] Sem PII no valor; miss reconstrói o SSOT
- [ ] Streams/filas não usam este porto (`reliable-messaging`)
- [ ] Memory* no unit; queda do Redis não derruba o request se a origem vive

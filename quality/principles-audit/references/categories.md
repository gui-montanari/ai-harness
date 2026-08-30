# Doze categorias — como varrer

A definição do princípio está no `AGENTS.md`. Aqui: **o que abrir e o que conta como achado**. Use o `inventory.json` como fila.

## 1. SSOT

Procure o mesmo fato em dois lugares:

- Fórmula, status machine, preço, desconto, timeout, tamanho de página
- Filtro de tenant no handler **e** de novo no repo **com lógica diferente**
- Campo com dois nomes sem anti-corruption (`accountId` no domínio lendo `externalCustomerId` cru)
- Frontend calculando o que o backend já decide
- Comentário/README que compete com o código (só é achado se **desvia** do código)

**Confirmação:** se a regra mudar, quantos diffs? >1 = achado.

## 2. DRY

Do `duplicates` do scanner, abra os pares. Classifique:

| Tipo | Ação |
|------|------|
| Decisão (if de regra, cálculo, authz) | achado `dry` (e talvez `ssot`) |
| Mapeamento mecânico DTO↔entidade | não é achado; anote como ok |
| Texto igual em testes | ok se for o mesmo cenário; extraia fixture se copiar 3+ |
| Gerado / vendored | N/A |

Não invente um `utils` para calar o achado. O dono é o módulo da regra.

## 3. SRP

Fila: `over_file`, `functions_over`, `classes_over`.

Para cada estouro: descreva a unidade **sem “e”**. Se não dá, é SRP, não “arquivo comprido”. A correção é fatiar por responsabilidade (nova porta, novo use case, novo arquivo de domínio) — não “parte 1 / parte 2”.

Handler que valida + aplica regra + formata e-mail + grava auditoria = SRP, mesmo com 80 linhas.

## 4. Hexagonal

Fila: `infra_imports` em `core`/`application` **e** leitura manual das pastas reais (o scanner erra camada se o repo não usa esses nomes — ajuste no `stack.md` e revia).

Achado quando:

- `core`/`domain` importa framework, ORM, Redis, HTTP client, SDK, React
- use case faz `new PostgresX()` / `get_engine()` / `fetch()`
- controller contém `if status ==` de negócio
- UI importa pacote de domínio do backend
- bounded context importa implementação de outro (não o contrato)
- não há composition root: concretos espalhados
- nomes do provedor (Stripe Invoice, WMS EmpresaId) no domínio
- `BaseModel` / Pydantic no use case, no domínio ou no mesmo arquivo que o `APIRouter`
- `*Command` / `*Result` / `@dataclass` no mesmo arquivo que o `execute` do caso de uso
- Command/Result em `application/schemas/` em vez de `application/commands/`
- classe `Memory*` ou adapter concreto em `application/`
- pastas MVC `models/` + `services/` no lugar de `core/domain/` + `application/`
- código de API e de UI misturados na raiz (`services/` + `apps/` sem `backend/` e `frontend/`)
- rota de negócio fora de `/api/v1`
- `os.environ` / `getenv` / `process.env` em `core/` ou `application/`
- `tenant_id="acme"` (ou o nome do produto) em worker, composition ou handler
- Smell `hardcoded_product_literal` / `hardcoded_config_default` / `hardcoded_localhost`
- Timeout, pool, lote, origin CORS, e-mail, token com default não-vazio no código de produção

**Não é achado:** enum de domínio, cópia canônica, fixture de teste, `tenant_id: str = ""` (recusa).
- adapter ou handler HTTP lendo env (fora de composition root, settings, entrypoint, migrate)
- smell do scanner `getenv_in_core_or_application` / `getenv_outside_composition`

Fila extra: `runtime_smells` com esses kinds. Composition (`di/`, `settings`, `app.py` de fábrica, worker, migrate) **pode** ler env. O resto recebe injetado.

**Protegido (ponto forte):** import-linter / dependency-cruiser no CI; porto em `core/ports`; adaptador em `infrastructure`; teste de contrato do adaptador.

## 5. TDD

Não dá para provar que o autor viu o vermelho no passado. Dá para provar o estado:

- Módulo de aplicação/domínio **sem** `tests/unit` correspondente
- Use case novo no diff (git) sem teste no mesmo diff — se a auditoria for de um PR
- Teste que mocka o SUT
- Regra só coberta por e2e
- `assert True` / teste que não quebra se apagar a implementação (faça o teste mental: delete a linha da regra; o teste falha?)

Olhe `tests/` vs `src/`. Liste use cases/handlers **sem** par de teste. Cada um é fila, não amostra.

## 6. Código morto

- Import/variável unused (ruff F401/F841, knip, eslint)
- Símbolo definido, zero referências (cuidado com DI por string e entrypoints)
- Bloco comentado, função `unused_*`, `if False`
- Feature flag default false sem caminho de remoção e sem leitor
- Rota registrada, zero cliente interno/externo visível no repo (informativa se for API pública)
- Teste de módulo que não existe

## 7. YAGNI / KISS

- Interface com **um** implementador e nenhum segundo previsto no plano
- `Base*FactoryAbstract` para um caso
- Event bus / outbox / saga para um único consumidor no mesmo processo
- Microserviço extra no compose sem bounded context real
- Flag “para o futuro”
- `dict[str, Any]` / `any` atravessando o domínio (KISS + solidez)

Não acuse de YAGNI um porto com um adaptador real + um fake de teste: isso é hexagonal.

Não acuse de YAGNI um **worker** no mesmo bounded context (API ≠ processo). Acuse um **microsserviço** extra sem o critério da constituição §8.2.

## 8. Segurança arquitetural (`security`)

Não substitui `/security-audit` (IDOR linha a linha, XSS, chaves, RLS). Aqui: o desenho **impede** a classe de falha.

Fila: handlers, use cases, compose, Dockerfiles, settings.

Achado quando:

- Default permissivo (segue sem tenant / sem auth)
- Tenant ou `user_id` vindo do body/query como fonte da verdade
- Papel checado só no frontend (aponte o handler sem guard)
- HTTP client / Redis / SMTP **sem timeout**
- Role de DB da app é superuser/owner
- Segredo em imagem, compose literal, log
- `except Exception: continue` em caminho autenticado
- Fetch de URL fornecida pelo usuário sem allowlist

Se o achado for um IDOR concreto com `arquivo:linha` de posse ausente: registre **aqui** se for padrão arquitetural (nenhum handler verifica posse) e deixe o detalhe rota-a-rota para `/security-audit` quando o humano pedir as duas. Não omita o padrão.

## 9. Escala / desacoplamento (`scalability`)

Fila: `docker-compose*`, `runtimes/`, `workers/`, charts, quem escreve em quais tabelas, HTTP entre serviços.

Achado quando:

- Trabalho pesado no request HTTP (PDF, ETL, fan-out) sem fila
- Worker e API no **mesmo processo**, estado na RAM (conexão websocket global, cache unbounded, “singleton” mutável)
- Coleção sem paginação; N+1 visível no use case/adapter
- Dois deployáveis com `import` de implementação ou **mesma tabela escrita pelos dois**
- HTTP síncrono em cadeia no hot path (A→B→C→D)
- Microsserviço extra **sem** fechar o critério §8.2 (ou worker idempotente ainda inexistente)
- Fila / buffer sem teto; `gather` sem limite
- Cache como fonte da verdade (sem TTL, sem invalidação)

**Protegido:** API e worker, mesma imagem, `command` diferente, réplicas do worker, contrato versionado, um escritor por agregado.

## 10. Resiliência (`resilience`)

Fila: compose/k8s `restartPolicy`, probes, entrypoint do worker, ACK da fila, testes de 2ª entrega.

Achado quando:

- Serviço sem política de restart
- Um container, vários processos (`supervisord` escondendo falha; `nohup`)
- ACK/commit da mensagem **antes** do efeito persistido
- Sem DLQ / retry infinito sem jitter
- Sem handler de SIGTERM (deploy mata no meio e some a mensagem, ou duplica)
- Liveness = ping no Redis/DB (blip derruba o cluster)
- Side-effect (cobrança, e-mail, WMS) sem chave de idempotência
- Sem teste da 2ª entrega do mesmo `message_id`

O scanner pode marcar `deploy.signals` (restart/health). Confirme no arquivo. Sem compose no repo: declare N/A da parte de orquestração; a idempotência do use case **ainda vale**.

## 11. Runtime (`runtime`) — async, tenant, semáforo, retry, idempotência

Constituição §8.6. Fila: `runtime_smells` do scanner + composition root + um use case típico + um consumer.

Achado quando a política **não tem dono global** ou o local **copia** em vez de herdar:

| Política | Achado |
|----------|--------|
| Async-only | `requests`, `time.sleep`, `readFileSync`, `execSync`, `psycopg2`/`subprocess.run` no path HTTP/worker |
| Tenant | `if order.tenant_id !=` em cada handler, cada um um pouco diferente; worker que roda sem restaurar contexto; job/export sem tenant |
| Semáforo | `asyncio.gather(*lista)` sem limite; `Semaphore(n)` solto no módulo; prefetch > budget |
| Retry | `for _ in range(3): try` no use case; retry de 4xx de negócio; sem jitter; `time.sleep` de verdade no teste |
| Idempotência | `processed = set()` em RAM; chave sem tenant; 2ª entrega duplica side-effect; store por use case em vez de um `IdempotencyStore` |

**Protegido:** um `RetryPolicy` + um `IdempotencyStore` + um contexto de tenant + semáforos no DI; adapters e consumers só recebem. Teste da 2ª entrega e teste de outro tenant no adapter.

Não acuse o fake de teste que implementa a mesma porta — isso é hexagonal. Acuse o segundo `retry()` escrito na mão.

## 12. Consistência (`consistency`) — nomes e schema/model

Constituição §3.1. Fila: um módulo antigo e um novo; `models.py`; tipos Pydantic/Zod vs ORM vs domínio.

Achado quando:

- Case fora da linguagem (`getOrder` em Python, `get_order` em TS)
- `HTTPClient` e `HttpClient` no mesmo repo
- Use case chamado `OrderService` / `*Utils` / `*Helper` com regra
- O mesmo tipo é entidade **e** row ORM **e** schema de API
- `models.py` (ou `types.ts`) mistura os três papéis
- Bounded context B usa pastas/sufixos diferentes do A sem plano
- Pydantic fora de `presentation/schemas/`; endpoint e DTO no mesmo arquivo
- Command em `application/schemas/` (colide com HTTP); o lugar é `application/commands/`
- Pasta `models/` ou `services/` no bounded context misturando entidade, DTO e caso de uso
- API e UI na raiz em vez de `backend/` e `frontend/`
- Arquivo de schema `001_*.sql`, `init.sql`, ou montado em `docker-entrypoint-initdb.d`
- Filename de migration que não casa `YYYYMMDD_VV__snake_description` (constituição §3.2)
- Prefixo `YYYYMMDD_VV` duplicado no repositório
- Compose/Makefile aplica dump (`psql < …`) em vez do runner
- Senha de role, token ou segredo no SQL da migration
- Dois runners (Alembic **e** SQL cru, Prisma **e** dump) no mesmo schema
- Prefixo da marca do produto em variável de ambiente (`TENDA_LLM_TOKEN`) — smell `product_brand_env`
- Prefixo do artefato de deploy (`WORKSPACE_DATABASE_URL`) — smell `deploy_unit_env`
- Schema SQL com nome de artefato (`CREATE SCHEMA workspace`) — smell `deploy_unit_schema`. Tabela de conversa é `agents.conversations`
- Nome de env que mudaria se o produto **ou a unidade de deploy** mudasse de nome
- Valor operacional literal (constituição §3.1 zero hardcode)

Fila extra: grep `os.environ` / `getenv` / `process.env` e as chaves do compose. Prefixo do repo (`tenda-communications` → `TENDA_`) e prefixo de artefato (`WORKSPACE_`, `PLATFORM_`, `MONOLITH_`) são achado. Provider de mercado (`OPENAI_API_KEY`, `TWILIO_AUTH_TOKEN`), `DATABASE_URL` deste processo, e bounded context alheio ainda falado daqui (`MESSAGING_DATABASE_URL`, `VAULT_DATABASE_URL`) são o padrão certo.

**Protegido:** `Order` no domain, `OrderRecord` no adapter, `OrderCreateRequest`/`OrderResponse` na borda; `CreateOrder` como use case; ruff/eslint no CI; migrations `YYYYMMDD_VV__…` aplicadas por um runner com ledger.

Correção: alinhar ao padrão **já usado no repo** (indústria da linguagem). Não inventar um quarto sufixo. Schema: um runner, filename §3.2.

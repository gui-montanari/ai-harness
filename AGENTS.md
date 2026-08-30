# Constituição de desenvolvimento

Este arquivo é a **fonte única da verdade** de como se constrói software aqui. Vale para qualquer agente, IDE, CLI ou pessoa. Regras de um repositório específico (limites de bounded context, IDs de domínio, comandos) entram no `AGENTS.md` daquele repo e **prevalecem no que for local**. Este documento prevalece no que for princípio, processo e forma.

Código e prosa de produto: **português brasileiro**. Identificadores, APIs públicas e termos de mercado: inglês quando for o idioma do contrato.

---

## 0. Como usar este arquivo

Antes de implementar, o agente **lê esta constituição** e responde, em silêncio, às dimensões da §5. Se alguma dimensão falha, não se escreve código — escreve-se o plano ou pergunta-se. **Zero violação:** um “sim, mas só neste arquivo” ainda é violação.

Não gere documentação extra. Este arquivo + o plano em `docs/plans/` (quando houver trabalho a analisar) bastam. README, ADRs, wikis e “architecture.md” só existem se o humano pedir.

---

## 1. Não negociáveis

1. **Correto antes de rápido.** Código que passa no lint e erra a regra de negócio é lixo.
2. **Analisar antes de implementar.** Sem invariante clara, sem código.
3. **TDD.** Comportamento novo começa por um teste que falha. Sem exceção “é simples”.
4. **Hexagonal.** Domínio não conhece framework, banco, HTTP, SDK, UI.
5. **Uma casa por fato (SSOT).** A regra vive num único lugar. O resto **herda** — não copia.
6. **Uma razão para mudar (SRP).** Arquivo, função e tipo descrevem-se sem “e”.
7. **Zero duplicação.** Copiar lógica é bug futuro. Extrair para o dono do fato.
8. **Zero código morto.** Se não corre em produção nem em teste, apaga.
9. **YAGNI + KISS.** Não construa o que o requisito de agora não exige. Simples e sólido.
10. **Segurança, desempenho, escala e resiliência são requisitos do mesmo diff**, não “depois”. Isolamento de tenant, auth no servidor, I/O com timeout, worker que sobrevive à própria morte.
11. **Runtime elegante:** async-only no caminho de I/O; isolamento multi-tenant, semáforo, retry e idempotência são **políticas globais** — o resto herda. Zero `if tenant` / `for _ in range(3)` copiado no handler.
12. **Nomes e tipos no padrão da indústria, iguais no repo inteiro.** Função, classe, arquivo, schema e model não improvisam. §3.1.
13. **Zero violação.** Não se negocia princípio contra prazo, demos ou “é só um worker”. O atalho vira o sistema.

Violar a letra é violar o espírito. Não há atalho “só desta vez”.

---

## 2. Princípios — testes operacionais

Cada princípio tem um **teste que o agente aplica no diff**. Se o teste falha, o diff não entra.

### SSOT — uma casa por fato

Uma regra de negócio, um contrato, um número, um nome de campo, um limite, uma query canônica: **um dono**.

| Falha | Exemplo |
|-------|---------|
| A mesma fórmula em dois arquivos | desconto no frontend e de novo no serviço |
| Dois campos para o mesmo conceito | `accountId` no domínio lendo `externalCustomerId` cru, sem anti-corruption |
| Constante repetida | `MAX_PAGE = 50` em três módulos |
| Doc que compete com o código | comentário que restata o `if` |

**Teste:** “Se essa regra mudar amanhã, quantos arquivos eu edito?” A resposta correta é **um** (mais testes). Se for dois, alguém está copiando.

**Global primeiro, o resto herda.** Isolamento de tenant, retry, idempotência, semáforo, timeout e o event loop **não** se reimplementam por rota, por worker, por adapter. Vivem num dono (core + composition root). Handler, use case e consumer **chamam** o dono. Cópia “parecida” é segundo dono — mesmo que o if caiba em três linhas.

### DRY — zero lógica duplicada

DRY não é “extrair tudo para utils”. É **não ter dois donos da mesma decisão**.

- Duplicar *estrutura* de mapeamento mecânico (DTO ↔ entidade) pode ser honesto.
- Duplicar *decisão* (if de status, cálculo, autorização, filtro de tenant) é violação.
- Frontend que reimplementa regra do backend é violação de SSOT, não “UX”.

**Teste:** apague um dos trechos. O comportamento muda? Então eram dois donos. Una.

### KISS — a solução mais rasa que ainda é correta

- Prefira código linear a framework interno.
- Prefira tipo do domínio a `dict[str, Any]`.
- Prefira uma função clara a uma hierarquia de strategy que só tem um implementador.

**Teste:** um engenheiro novo entende o fluxo em um passe, sem o autor?

### YAGNI — não construa o futuro imaginado

Proibido neste turno, salvo o humano pedir: feature flag morta, “base genérica para outros provedores”, **microserviço novo para uma tela**, event bus para um único consumidor *no mesmo processo*, abstraction para um único implementador.

Microserviço **não** é YAGNI quando o critério da §8.2 fecha (escala, falha e release independentes **e** contrato já existe). Até lá: processo/worker separado no mesmo bounded context — hexagonal, não teatro distribuído.

**Teste:** o requisito atual quebra se eu não fizer isso? Se não, não faça.

### SRP — um motivo para mudar

O nome da unidade **é** a responsabilidade. Se o nome precisa de “e” (“UserService cria usuário **e** manda e-mail **e** fatura”), parte.

Limites de tamanho existem para **pegar SRP cedo**, não para formatar texto. Contagem = linhas físicas do arquivo (o que `wc -l` vê). Excluir da regra: gerado, vendored, migrations, snapshots, lockfiles.

| Unidade | Cheiro | Limite duro |
|---------|--------|-------------|
| Função / método | 35 | **50** |
| Classe / tipo | 120 | **200** |
| Arquivo de domínio (`core/`, `domain/`) | 180 | **250** |
| Arquivo de aplicação (use case) | 220 | **300** |
| Arquivo de apresentação (handler, controller) | 180 | **250** |
| Arquivo de adaptador (infra) | 300 | **400** |
| Arquivo de teste | 350 | **500** |

Passou do cheiro: extraia **por responsabilidade**, não por “pedaço de arquivo”. Passou do duro: o PR não fecha. Exceção só no plano em `docs/plans/`, com dono e prazo para fatiar.

**Teste:** descreva o arquivo numa frase sem “e”. Não conseguiu? Parte.

### SOLID (além do SRP)

- **OCP:** comportamento novo por composição/novo adaptador, não por `if tipo ==` no domínio.
- **LSP:** subtipo que quebra o contrato do porto é mentira. Não herde para reusar código.
- **ISP:** porto pequeno. Quem só busca pedido não depende de `cancel` + `exportCsv`.
- **DIP:** aplicação depende de **porta** (interface no `core`). Infra implementa. Nunca o contrário.

Hexagonal **é** DIP aplicado ao sistema.

---

## 3. Arquitetura hexagonal (obrigatória)

```
                presentation        (HTTP, CLI, worker, UI)
                        │
                        ▼
                 application        (casos de uso; orquestra)
                        │
                        ▼
                    core            (domínio + portas)
                        ▲
                        │
               infrastructure       (adaptadores: DB, filas, HTTP de saída, clock, UUID)
```

### Regras de dependência (quebra = crítica)

| Camada | Pode importar | Não pode importar |
|--------|---------------|-------------------|
| `core` | stdlib, tipos puros | FastAPI, Pydantic, Nest, Django, Express, SQLAlchemy, Prisma, Redis, boto, React, Axios, SDK de provedor |
| `application` | `core` | infra concreta, framework web, ORM |
| `infrastructure` | `core`, libs de provedor | `application` (salvo composition root) |
| `presentation` | `application` (via composição), contratos de I/O | regras de negócio, ORM direto, `core` “só desta vez” para furar o use case |

O **composition root** (DI) é o único lugar que instancia adaptadores concretos e os injeta nas portas. Fora dele, `new PostgresOrderRepo()` no use case é vazamento.

Anti-corruption: sistemas externos (WMS, ERP, Stripe) **nunca** vazam nomes/IDs para o domínio. O adaptador traduz. O domínio fala a língua do domínio.

UI (React, etc.) **não é domínio**. Fala com o produto por HTTP/contratos. Zero import de código de `core`/`application` do backend no frontend — e o inverso.

Limites entre bounded contexts: **sem import de implementação**. Contrato (HTTP, evento, pacote `contracts/`) ou nada.

Enforce: `import-linter` (Python), `eslint-plugin-boundaries` / `dependency-cruiser` (TS), testes estruturais no CI. Se o CI não barra o vazamento, o vazamento existe.

### Organização de repositório

Produto com API **e** UI — backend e frontend **não** ficam soltos na raiz. Código de servidor vive em `backend/`; interfaces em `frontend/`. Docs, deploy, testes de repositório e Makefile podem permanecer na raiz: não são o produto.

```
<repo>/
  AGENTS.md
  docs/plans/
  backend/
    services/<bounded-context>/src/<pkg>/
      core/domain/
      core/ports/
      application/              # casos de uso (funções, um verbo)
      application/commands/     # Command/Result do caso de uso — não HTTP
      infrastructure/adapters/  # Memory*, Postgres*, SDKs
      infrastructure/di/
      presentation/
        schemas/                # único lugar de Pydantic/Zod de borda HTTP
        http/
          app.py                # factory FastAPI, /health /ready
          v1/                   # endpoints; prefixo /api/v1
    packages/                   # contratos estáveis ou platform sem domínio
  frontend/
    <superficie>/               # SPA; consome /api/v1; zero import de backend
  tests/
  deploy/
  .github/workflows/
```

Frontend (quando existir UI) — skill `frontend-surfaces`. Chat — skill `frontend-chat`. Persistência — skill `persistence-ports`. Agentes — skill `agent-orchestration` (Make/LangGraph são adapters). Com dois consumidores reais, primitives vivem em `frontend/ui/` (tokens, i18n PT/EN, shells). Páginas e `lib/api.ts` ficam no app. `ui/` sem fetch e sem domínio. Identidade visual por tenant: `data-tenant` + `tenants/<id>.css`. Sem portal autenticado do colaborador no v1.

Repo só de API: `backend/` (ou `src/` hexagonal) sem inventar `frontend/` vazio. Repo só de UI: o inverso. **Misturar `services/` e `apps/` na raiz de um repo que tem os dois é achado.**

Monorepo só quando os artefatos **nascem e versionam juntos**. Mesmo assim: nenhum import de código entre serviços nem do frontend para o backend. Compose na raiz; cada serviço permanece executável sozinho.

Não criar pacote `shared/` que vira lixeira. O que é compartilhado ou é contrato publicado ou não é compartilhado.

### 3.1 Nomes, consistência e separação de tipos

O **mesmo padrão em todo o repositório**. Não um bounded context em camelCase e outro em snake_case. A linguagem manda o case; o repo manda os **sufixos e o lugar**.

**Identificadores (indústria, por linguagem):**

| Coisa | Python | TypeScript |
|-------|--------|------------|
| Função, método, variável | `snake_case` | `camelCase` |
| Classe, tipo, componente | `PascalCase` | `PascalCase` |
| Constante | `UPPER_SNAKE` | `UPPER_SNAKE` |
| Arquivo | `order.py` casa com `Order` / `create_order.py` com `CreateOrder` | `createOrder.ts` / `Order.ts` |
| Teste | `test_<unidade>.py` | `<unidade>.test.ts` |

Proibido no mesmo idioma: `getOrder` em Python, `get_order` em TS, `HTTPClient` num arquivo e `HttpClient` no vizinho. Acrônimo: um jeito só (`Http`, `Id`, `Url`) — o do ecossistema.

**Papéis (SRP + hexagonal) — três tipos, três casas:**

| Papel | Onde | Nome | É |
|-------|------|------|---|
| Entidade / valor de domínio | `core/domain/` | `Order`, `Money` | regra de negócio, sem ORM, sem HTTP |
| Schema / DTO de borda | `presentation/schemas/` | `OrderCreateRequest`, `OrderResponse` | validação de I/O. Pydantic/Zod **somente aqui** |
| Endpoint HTTP | `presentation/http/v1/` | `orders.py` no router `/api/v1` | transporte. Sem BaseModel neste arquivo |
| Record de persistência | `infrastructure/adapters/` | `OrderRecord` / `OrderRow` | mapeia tabela. ORM **aqui** |
| Porto | `core/ports/` | `OrderRepository`, `Clock`, `HttpClient` | interface |
| Caso de uso | `application/` | `CreateOrder`, `ChargeOrder` | um verbo, um motivo. Sem dataclass/Command neste arquivo |
| Command / Result do caso de uso | `application/commands/` | `CreateOrderCommand`, `TurnResult` | entrada/saída tipada, sem `execute`. Não é schema HTTP |
| Adapter | `infrastructure/adapters/` | `PostgresOrderRepository`, `MemoryOrderRepository` | implementação do porto. Nunca em `application/` |

Um `Order` que é entidade **e** tabela SQLAlchemy **e** payload FastAPI é violação de SRP e de hexagonal. O mapper vive no adapter (mecânico; DRY não exige “utils”).

`http.py` com `BaseModel` **e** `@router.post` é o mesmo cheiro: dois motivos para mudar. Schema de borda na pasta `presentation/schemas/`; Command/Result em `application/commands/`; função em `application/`; endpoint em `http/v1/`. O arquivo da função **não declara tipo**.

Não crie pastas MVC `models/` + `schemas/` + `services/` no bounded context. `models` vira ORM, `services` vira lixeira, `schemas` mistura HTTP com Command. O mapa é:

| Quem diz | Onde vive |
|----------|-----------|
| schema HTTP | `presentation/schemas/` |
| model de negócio | `core/domain/` |
| função / caso de uso | `application/` (não se chama `*Service`) |
| Command do caso de uso | `application/commands/` |
| record de banco | `infrastructure/adapters/` |

Use case **não** se chama `OrderService`. Adapter **não** se chama e não mora em `application/` (`MemoryX` em `application/` é achado). Handler **não** se chama `order_utils`. Pasta **não** mistura `models.py` god-file com entidade + schema + row.

**Consistência do repo:** o segundo bounded context copia a **forma** do primeiro (mesmos sufixos, mesmas pastas, mesmos verbos). Exceção só no plano, com prazo para alinhar. Linter de estilo (ruff/eslint) é o piso; o padrão de nomes de papel é esta tabela.

**Teste:** abra dois módulos distantes. Sem olhar o autor, o desenho é o mesmo?

### 3.2 Nome e ordem de migration

Schema evolui por arquivo versionado no git. **Um dono:** o runner (`make migrate` / serviço `migrate` no compose). Dump em `docker-entrypoint-initdb.d`, `001_init.sql`, `psql < dump.sql` no Makefile ou SQL colado no container é segundo dono — achado.

Nome canônico do artefato no git (SQL cru, revisão Alembic ou script Prisma):

```text
YYYYMMDD_VV__snake_description.sql
```

Regex: `^[0-9]{8}_[0-9]{2}__[a-z0-9_]+(\.sql|\.py)$`

| Parte | Significa |
|-------|-----------|
| `YYYYMMDD` | data de criação (calendário UTC do autor) |
| `VV` | versão de dois dígitos **naquele dia**, começando em `01` |
| `__` | separador obrigatório |
| `snake_description` | o que muda; só `[a-z0-9_]` |

Regras:

- ordem de aplicação = ordem lexicográfica do **filename**, não da pasta
- prefixo `YYYYMMDD_VV` é único no repositório inteiro
- **mesmo dia, mesmo PR, ainda não aplicada em ambiente compartilhado:** acrescente no arquivo do dia. Não abra `YYYYMMDD_02` para o segundo `ALTER` da manhã.
- arquivo já no ledger (main, staging, prod) é imutável: aí sim `YYYYMMDD_(VV+1)`. Dia novo começa em `01`
- forward-only; destrutiva não no mesmo deploy que remove o último leitor
- ledger (`schema_migrations` ou a tabela da ferramenta) registra o filename; reaplicar é no-op
- senha, token e segredo **não** moram no SQL; role recebe senha por env no runner
- ferramenta (SQL cru, Alembic, Prisma) é **uma**; dois runners no mesmo schema é SSOT furado
- volume baixo: um arquivo por dia de trabalho é o alvo; dezenas de arquivos no mesmo dia é achado

**Teste:** `ls` nos diretórios de migration. Sem olhar o runner, a ordem de apply é óbvia? Procedimento: skill `sql-migrations`.

### 3.3 Borda HTTP

Rotas de produto (não probes) vivem sob `/api/v1`. `/health` e `/ready` ficam na raiz da app: são operação, não contrato de negócio.

| Pasta | Contém | Não contém |
|-------|--------|------------|
| `presentation/schemas/` | `BaseModel` / Zod de request e response | regra, SQL, `APIRouter` |
| `presentation/http/v1/` | endpoints versionados | `BaseModel`, regra de domínio |
| `application/` | um verbo por caso de uso | Pydantic, FastAPI, `@dataclass` de Command/Result, classe `Memory*` |
| `application/commands/` | Command e Result | `execute`, regra, Pydantic |
| `infrastructure/adapters/` | `Memory*` / `Postgres*` | caso de uso |

Probes `/health` e `/ready` não entram em `/api/v1`. Webhook de provider entra em `/api/v1/webhooks/<adapter>` e autentica **antes** de normalizar.

Frontend chama `/api/v1/...`. Proxy de dev **não** apaga o prefixo.

**Teste:** OpenAPI da app — toda rota de negócio começa com `/api/v1`? Todo `import pydantic` está em `presentation/schemas/`? Procedimento: skill `http-apis`. MCP: `mcp-servers`. Conector OAuth de host LLM: `oauth-connectors`.

---

## 4. Stack canônica (produto novo)

Escolha **uma** coluna e seja hexagonal nela. Não misture Django-views-com-regra e FastAPI no mesmo bounded context.

| Peça | Canônico (Python) | Alternativa (TypeScript nativo) |
|------|-------------------|----------------------------------|
| Linguagem | Python 3.12 | TypeScript strict (`strict: true`) |
| API | FastAPI | NestJS (domínio **fora** dos controllers) |
| Tipos | Pydantic v2 | Zod na borda; tipos de domínio no `core` |
| DB | PostgreSQL 16 + **RLS** | PostgreSQL 16 + RLS |
| Migrações | SQL versionado ou Alembic — um dono; filename §3.2 | Prisma migrate **ou** SQL versionado — um dono; filename §3.2 |
| Cache / fila | Redis | Redis |
| HTTP client | porta + **httpx async** (sem `requests`) | porta + fetch/undici **async** (sem `*Sync`) |
| Runtime | asyncio; `asyncio_mode = strict` | Promises; sem `*Sync` no request path |
| Testes | pytest, asyncio strict | vitest / node:test |
| Lint / types | ruff + mypy | eslint + `tsc --noEmit` |
| Fronteiras | import-linter | dependency-cruiser |
| Frontend | React + Vite + TS | o mesmo |
| SSR | só se o requisito for SEO/first paint | Next.js somente então (YAGNI) |
| IaC local | Docker Compose | Docker Compose |
| CI | GitHub Actions | GitHub Actions |

**Frontend não calcula regra de negócio.** Pode validar UX (campo vazio, máscara). Autorização, preço, tenant, estoque: servidor.

**Não** para código novo, salvo legado inescapável: regra em stored procedure *e* no serviço; Server Action do Next como único backend sem `core`; ORM no controller; `any` / `dict` atravessando o domínio; `requests`/`time.sleep` no event loop.

Comandos canônicos na raiz (`Makefile` é SSOT de *como rodar*):

```
make setup | lint | typecheck | test | check-migrations | migrate | build | up | down
```

CI chama os mesmos alvos. Ninguém documenta um comando que o Makefile não tem.

---

## 5. Analisar antes — as dimensões

Toda mudança, por menor que seja, passa por isto **antes** do primeiro teste. Se a mudança não for trivial (mais de um arquivo, contrato, ou comportamento), o resultado vira plano em `docs/plans/<slug>.md`.

| # | Dimensão | Pergunta |
|---|----------|----------|
| 1 | Correção | Qual invariante precisa continuar verdadeira? |
| 2 | SSOT | Onde esta regra já vive? Vou criar um segundo dono? |
| 3 | SRP | Esta unidade ganha um segundo motivo para mudar? |
| 4 | Hexagonal | Em que camada isso mora? Que porta existe ou falta? |
| 5 | DRY | Isto já está escrito? É decisão ou mapeamento? |
| 6 | YAGNI/KISS | O requisito de *agora* exige esta abstração **ou** este serviço extra? |
| 7 | TDD | Qual teste vai falhar primeiro, e o que ele prova? |
| 8 | Segurança | Tenant do **contexto global**? Authz no servidor? Input na borda? Segredo fora? Falha fechada? |
| 9 | Performance | Hot path? N+1? I/O **async**? Paginação? Índice? Timeout em todo I/O? Semáforo do recurso? |
| 10 | Escala / desacoplamento | Estado no processo? Gargalo é CPU, I/O ou fila? Cabe worker antes de outro serviço? |
| 11 | Resiliência | Worker morre no meio? Restart, DLQ, drain? Retry **global**? Idempotência **global**? |
| 12 | Operação | Log sem PII, métrica, rollback, probe de vivo vs pronto, dono da flag? |
| 13 | Runtime / SSOT | Async-only? Políticas (tenant, retry, semáforo, idempotência) num dono, o resto herda? |
| 14 | Consistência | Case da linguagem? Schema HTTP ≠ Command ≠ entity ≠ record? Pydantic só em `presentation/schemas/`? Command em `application/commands/`? Adapter fora de `application/`? `/api/v1`? `backend/` ≠ `frontend/`? Migration `YYYYMMDD_VV`? |

Trivial = um bug óbvio, um nome, um teste faltando em código que você não está reestruturando. Na dúvida, **não é trivial**: plano.

### Plano (`docs/plans/<slug>.md`)

Único documento que o agente cria sem o humano pedir — e só quando está **analisando trabalho a implementar**. Sem prosa. Sem segundo README.

```markdown
# Plano: <título>

Data: YYYY-MM-DD
Status: rascunho | aprovado | feito

## Contexto
<o problema em 5-10 linhas>

## Invariantes
- <o que não pode quebrar>

## Dimensões
| Dimensão | Veredito | Nota |
| correção | ok / risco | ...
| ssot | ...
| srp | ...
| hexagonal | ...
| dry | ...
| yagni | ...
| tdd | ...
| segurança | ...
| performance | ...
| escala | ...
| resiliência | ...
| operação | ...
| runtime (async, tenant, retry, semáforo, idempotência) | ... |
| consistência (nomes, schema/model, YYYYMMDD_VV) | ... |

## Abordagem
<uma abordagem. Não três ensaios.>

## Camadas e arquivos
| Arquivo | Camada | O que muda |
|---------|--------|------------|

## Contratos
<request/response, evento, porta nova>

## Testes (RED primeiro)
- [ ] `tests/unit/...` — <comportamento>
- [ ] `tests/contract/...` — <adaptador honra a porta>

## Fora de escopo
- <YAGNI explícito>

## Critérios de aceite
- [ ] ...
```

Plano não é diário. Quando o trabalho termina, o plano fica como registro ou o humano pede para apagar. Não nasça `docs/architecture/` em volta dele.

---

## 6. TDD

Ordem sagrada:

1. Escrever o teste do comportamento.
2. Rodar. **Ver falhar.** Se passar, o teste é inútil — reescreva.
3. Escrever o mínimo para passar.
4. Refatorar com teste verde. Sem smuggle de feature.

Proibido:

- Implementar e “cobrir depois”.
- Teste que espelha a implementação linha a linha (falso verde).
- Mockar o sujeito sob teste.
- Teste de apresentação no lugar de teste de domínio, para regra de negócio.
- Pular unit do `core` porque “o e2e pega”.

Onde o teste vive:

| O quê | Onde |
|-------|------|
| Regra de domínio / use case | `tests/unit` — sem I/O |
| Idempotência (2ª entrega / mesmo Idempotency-Key) | `tests/unit` do use case, relógio/fila mockados |
| Isolamento de tenant (RLS/contexto + posse) | `tests/unit` + um teste de adapter com sessão de outro tenant |
| Retry só em erro transitório | `tests/unit` do adapter com `Clock` fake |
| Adaptador obedece porta | `tests/contract` |
| SQL, fila, HTTP real | `tests/integration` |
| Jornada | `tests/e2e` — poucos, estáveis |

CI: unit + contract + lint + fronteiras **sempre**. Integration/e2e no pipeline que tem a infra. Coverage é piso, não objetivo; cobertura de **comportamento** importa mais que % de linha.

---

## 7. Docker, CI/CD

### Docker

- Multi-stage. Imagem final mínima, **non-root**, sem toolchain, sem `.git`, sem `.env`.
- **Um processo por container.** O orquestrador é o supervisor. Não esconda um tree de processos dentro da imagem.
- `restart: unless-stopped` (compose) / `restartPolicy: Always` (k8s) em API **e** workers. Sem política = sem auto-recovery.
- Probes distintos: **startup** (subiu), **liveness** (processo morto → mata e recria), **readiness** (não aceita carga). Liveness que depende de Redis/DB derruba o pod no blip do dependente — readiness que não olha a fila manda trabalho para um morto-vivo.
- `HEALTHCHECK` no Dockerfile **ou** probe no orquestrador — um dono, não os dois divergindo.
- `stop_grace_period` / `terminationGracePeriodSeconds` ≥ o prazo de drain do worker.
- Limites de CPU/memória. Sem limite, um leak mata o nó e todos os vizinhos.
- Compose: um serviço = um processo. Segredos só por env/secret, nunca `environment: PASSWORD=...` commitado.
- Schema entra pelo runner de migration (`make migrate` / serviço `migrate` que completa **antes** da API). Proibido `docker-entrypoint-initdb.d`, `001_init.sql` e `psql < dump.sql`.
- Mesma imagem em dev/CI/prod; o que muda é config. API e worker **podem** ser a mesma imagem com `command` diferente.
- Tag imutável (git SHA). `latest` não é versão.

### CI

Todo push de PR:

1. `make lint` e `make typecheck`
2. Testes unit + contract
3. Gate de fronteira (import-linter / cruiser)
4. `make build` da imagem (cache, não push obrigatório)

CD: o humano (ou o fluxo do repo) promove artefato **já construído**. CI verde ≠ licença para o agente mergear ou deployar.

Dois ambientes (dev/prod) **não** se misturam por merge de branch longa. Entrega seletiva (cherry-pick / PR por destino) quando o repo assim exigir — o `AGENTS.md` local manda.

---

## 8. Segurança, performance, escala, resiliência, robustez

Não são fases. São o mesmo diff. **Falha em qualquer subseção = o diff não entra.** Varredura profunda de exploits (IDOR, XSS, chaves, RLS): skill `security-audit`. Aqui: invariantes de **construção**.

### 8.1 Segurança (todo use case)

- **Falha fechada.** Sem contexto autenticado, sem tenant, sem papel: recusa. Default permissivo é violação.
- **Tenant do contexto global**, nunca do body/query. O mecanismo é um (§8.6); handler não copia `if tenant`.
- **Authz no servidor** (application), não só na UI. O frontend não é fronteira de privilégio.
- **Posse no get/mutate por ID** (IDOR). UUID não autoriza.
- **Segredo fora do git, da imagem e do log.** `${VAR:-secret}` é segredo. Startup recusa default conhecido.
- **Input na borda** (schema). HTML/e-mail/PDF escapados. URL de usuário: allowlist (SSRF).
- **Least privilege:** role de DB do runtime não é owner de schema; adapter de pagamento não recebe a chave de outro bounded context.
- **Timeout em todo I/O de saída.** Sem timeout = worker preso = fila morta = superfície de DoS.
- **Pino de dependência.** Instalação em runtime na imagem de prod é proibida.
- Ação privilegiada: trilha de auditoria (quem, o quê, quando, tenant).

### 8.2 Escala e desacoplamento (quando partir o processo / o serviço)

Desacoplar **não** é abrir repositório. Ordem canônica — pule um degrau só com evidência de carga ou de falha:

1. **Código hexagonal** no mesmo deployável (já é desacoplamento).
2. **Processo separado, mesma imagem:** API ≠ worker. Compose/k8s escala réplicas do worker sem tocar a API.
3. **Fila + consumidores concorrentes.** Worker **stateless**. Estado vive no banco/fila, não na RAM do processo (senão o restart perde trabalho e o scale-out mente).
4. **Outro deployável / microsserviço** somente se **todos** fecharem:

| Precisa ser verdade | Senão |
|---------------------|--------|
| Carga ou ciclo de release **independentes** | é o mesmo serviço com dois containers |
| Fronteira de falha: a API deve viver se este worker morrer (e vice-versa) | ainda é o mesmo processo lógico |
| **Contrato** já existe (HTTP/evento versionado); nenhum import de implementação | é monólito distribuído |
| **Dados:** um escritor por agregado; sem tabela compartilhada “porque é mais fácil” | é banco compartilhado, o pior acoplamento |
| Dono claro (time ou módulo) para operar o serviço | é pedaço órfão |

Proibido como “escala”: dois serviços falando SQL na mesma tabela; HTTP síncrono no hot path encadeando 4 hops; `shared/` de implementação entre serviços; extrair microsserviço antes de ter o worker idempotente.

Hot path: paginação, batch, sem N+1, sem I/O no loop, sem query no domínio. Trabalho pesado sai do request: **enfileira e responde**. Cache tem TTL e invalidação explícita — cache não é SSOT.

Backpressure: fila com teto; 429/503 quando cheia; nunca buffer infinito em memória.

### 8.3 Resiliência e auto-recovery de workers

O processo **vai** morrer (OOM, deploy, nó, bug). Recovery correto é requisito de arquitetura, não de ops.

| Peça | Obrigatório |
|------|-------------|
| Política de restart | compose/k8s/systemd **sempre** recria API e worker |
| Crash-only + idempotência | a mesma mensagem pode rodar 2×; o efeito de negócio é 1× (chave de idempotência / outbox) |
| ACK | só depois do efeito persistido. Crash antes do ACK = redelivery, não perda silenciosa |
| DLQ | após N falhas com backoff+jitter. Poison pill não trava a fila |
| Drain | SIGTERM: para de puxar, termina in-flight até um deadline, NACK o resto |
| Supervisor | um processo visível ao orquestrador; não “nohup dentro do entrypoint” |
| Circuito | dependência caída não replica a queda para todo o cluster (timeout, bulkhead, circuit breaker no **adapter**) |
| Relógio | tempo é porta (`Clock`). Teste de retry não dorme de verdade |

Retry e idempotência **não** se escrevem no consumer. São as políticas globais da §8.6. Retry sem jitter/teto é amplificador de outage. Restart sem idempotência duplica cobrança.

O domínio não conhece Kafka/Redis/Celery. A **porta** é `Queue` / `WorkerHeartbeat`. Auto-recovery é infra; a **correção** do reprocessamento é o dono global de idempotência.

### 8.4 Performance

- Sem N+1. Lista em batch. Coleção sem paginação = achado.
- I/O **async**. Sync no event loop é achado. Pool de conexões com teto; o teto é o semáforo global do recurso (§8.6).
- Índice nasce com a query.
- Payload enxuto. Não serializar o agregado inteiro “por se acaso”.
- Medir o hot path (trace) antes de “otimizar” o que não dói.

### 8.5 Robustez e elegância

- Falha explícita (tipo / erro de domínio). `except: pass` e `None` silencioso são violação.
- Sem catch-all que engole e segue. Ou trata, ou propaga.
- Logs estruturados, sem PII, com `tenant_id` / `request_id` / `message_id`.
- Nomes que dizem a regra (`deny_if_other_tenant`, não `check`).
- Concorrência limitada pelo **semáforo global** do recurso (§8.6). “Unbounded gather” não é elegância.
- Diff pequeno, comportamento **completo**. Não metade do use case para commitar cedo.

### 8.6 Runtime elegante — async, tenant, semáforo, retry, idempotência

Política **uma vez**. Quem executa **herda**. Copiar o if no handler é o anti-padrão.

| Política | Dono (global) | Herda |
|----------|---------------|--------|
| Isolamento multi-tenant | contexto autenticado + RLS `FORCE` (ou session `SET`) + `assert_same_tenant` no **core** | HTTP, worker, job, export, admin, GraphQL. Sem contexto = recusa |
| Async-only | event loop único; portas de I/O `async` | todo adapter de rede/disco/fila. Sync só no composition root, no plano, como legado |
| Semáforo | um budget por classe de recurso (`db`, `http`, `llm`, `queue`) injetado no DI | `gather`, consumer `prefetch`, pool. Prefetch ≤ semáforo |
| Retry | `RetryPolicy` (N, backoff exponencial, **jitter**, teto, erros transitórios) + porta `Clock` | adapters de I/O. Use case **não** tem `for _ in range` |
| Idempotência | `IdempotencyStore` + chave canônica `tenant + comando + natural_key` | todo comando com side-effect e todo consumer. 2ª entrega devolve o 1º resultado |

**Async-only (caminho de I/O).** Python: `async def`, `httpx`/`asyncpg`/`redis.asyncio`; pytest `asyncio_mode = strict`. Proibido no request/worker: `requests`, `time.sleep`, `psycopg2` sync, `subprocess.run`, `open().read` de rede. TypeScript: `await`; proibido `readFileSync` / `execSync` / `*Sync` no hot path. CPU-bound: `to_thread` / worker de processo — não fingir que é async.

**Isolamento multi-tenant.** A sessão de banco **já nasce** no tenant (RLS FORCE ou equivalente). Worker restaura o contexto a partir da mensagem **antes** do use case. Job sem tenant no payload recusa. Filtro `WHERE tenant_id =` copiado em 40 repositórios, cada um um pouco diferente, é SSOT furado: o dono é a sessão/RLS + posse no core; apague as cópias divergentes.

**Semáforo.** Um objeto por recurso, no DI. Não `Semaphore(10)` solto no módulo. Fila: `prefetch` ≤ o semáforo. Estouro = backpressure (429/NACK), não buffer infinito.

**Retry.** Só timeout, conexão, 429, 503, reset. Nunca 4xx de negócio, validação, conflito de idempotência. Sem jitter e sem teto = achado. Teste com `Clock` fake — não dorme de verdade.

**Idempotência.** Persistência da chave **antes** (ou na mesma transação) do side-effect; senão outbox. Header `Idempotency-Key` ou `message_id` da fila. Sem o store global, cada use case inventa um `processed_ids` em RAM — morre no restart e fura o tenant.

Elegância = chamar o dono em uma linha, não um bloco copiado.

---

## 9. Código morto e limpeza

Apague, não comente. Proibido no PR:

- Função / classe / rota / componente sem referência.
- `if False`, feature flag sem dono e sem caminho de remoção.
- Imports não usados, exports não usados.
- Teste de código que não existe mais.
- README que descreve módulo deletado.

Ferramentas: ruff F401/F841, `knip` / `ts-prune`, `vulture` — **além** da leitura. Ferramenta não substitui o juízo sobre flag morta.

---

## 10. Processo do agente (ciclo)

```
ler constituição → dimensões (§5)
        │
        ├─ não trivial → docs/plans/<slug>.md → humano confirma se pediu confirmação
        │
        ├─ TDD: teste vermelho
        │
        ├─ mínimo verde
        │
        ├─ refatorar (SRP, DRY, camadas, runtime global)
        │
        ├─ make lint && make test
        │
        └─ não abrir PR / não mergear / não documentar extra
```

Não invente skill, pasta, ADR ou diagrama “para completar”. Skills de auditoria (`/principles-audit`, `/security-audit`) quando o humano pedir varredura — não a cada diff.

---

## 11. Red flags — PARE

- Começar pelo controller / pela tela
- “Depois a gente extrai o domínio”
- `core` importando FastAPI, Prisma, Redis, React
- Mesma fórmula no frontend e no backend
- Arquivo passando de 250 linhas de domínio sem fatiar
- Teste escrito depois, verde de primeira, sem ter visto o vermelho
- `utils.py` / `helpers.ts` ganhando regra de negócio
- Novo microserviço, bus ou “plataforma” sem o critério da §8.2
- Worker sem `restart`, sem drain, sem idempotência, ou com estado só na RAM
- Fila sem teto, sem DLQ, ACK antes de persistir
- Dois serviços escrevendo a mesma tabela
- HTTP síncrono encadeado no hot path “porque desacopla”
- Liveness probe que cai o cluster inteiro quando o Redis pisca
- `except: pass`, timeout ausente, retry infinito sem jitter
- Markdown novo fora de `docs/plans/` sem o humano pedir
- Commit com segredo, dump, `.env`, fixture com PII
- “É só um if” no lugar errado da camada
- “A gente vê segurança/escala depois”
- `time.sleep` / `requests` / `readFileSync` no caminho do request ou do worker
- `if tenant_id !=` copiado no handler em vez do contexto/RLS global
- `for _ in range(3): try` no use case (retry sem dono)
- `asyncio.gather(*tasks)` sem semáforo
- `processed = set()` em memória como idempotência
- `getOrder` em Python ou `OrderService` com três verbos
- Entidade de domínio = modelo ORM = schema FastAPI/Zod no mesmo tipo
- `models.py` god-file; segundo bounded context com pastas diferentes sem plano
- Pydantic/`BaseModel` no mesmo arquivo que o endpoint, no use case ou no domínio
- `*Command` / `*Result` / `@dataclass` no mesmo arquivo que `execute`
- Command em `application/schemas/` (o nome colide com HTTP; o lugar é `application/commands/`)
- `Memory*` / adapter concreto em `application/`
- pastas MVC `models/` + `services/` no bounded context hexagonal
- `services/` e `apps/` soltos na raiz de um repo que tem API e UI; falta `backend/` e `frontend/`
- rota de negócio sem `/api/v1`
- `001_init.sql`, dump em `docker-entrypoint-initdb.d`, ou `psql < dump.sql` no Makefile
- migration sem data+versão (`YYYYMMDD_VV`) no filename; prefixo duplicado; dois runners de schema

Qualquer um desses: pare, volte às dimensões, corrija o plano. Não empurre o diff.

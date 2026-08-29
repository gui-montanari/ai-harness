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
5. **Uma casa por fato (SSOT).** A regra vive num único lugar. O resto lê esse lugar.
6. **Uma razão para mudar (SRP).** Arquivo, função e tipo descrevem-se sem “e”.
7. **Zero duplicação.** Copiar lógica é bug futuro. Extrair para o dono do fato.
8. **Zero código morto.** Se não corre em produção nem em teste, apaga.
9. **YAGNI + KISS.** Não construa o que o requisito de agora não exige. Simples e sólido.
10. **Segurança, desempenho, escala e resiliência são requisitos do mesmo diff**, não “depois”. Isolamento de tenant, auth no servidor, I/O com timeout, worker que sobrevive à própria morte.
11. **Zero violação.** Não se negocia princípio contra prazo, demos ou “é só um worker”. O atalho vira o sistema.

Violar a letra é violar o espírito. Não há atalho “só desta vez”.

---

## 2. Princípios — testes operacionais

Cada princípio tem um **teste que o agente aplica no diff**. Se o teste falha, o diff não entra.

### SSOT — uma casa por fato

Uma regra de negócio, um contrato, um número, um nome de campo, um limite, uma query canônica: **um dono**.

| Falha | Exemplo |
|-------|---------|
| A mesma fórmula em dois arquivos | desconto no frontend e de novo no serviço |
| Dois campos para o mesmo conceito | `accountId` e `stockfyClienteId` sem anti-corruption no adaptador |
| Constante repetida | `MAX_PAGE = 50` em três módulos |
| Doc que compete com o código | comentário que restata o `if` |

**Teste:** “Se essa regra mudar amanhã, quantos arquivos eu edito?” A resposta correta é **um** (mais testes). Se for dois, alguém está copiando.

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
| `core` | stdlib, tipos puros | FastAPI, Nest, Django, Express, SQLAlchemy, Prisma, Redis, boto, React, Axios, SDK de provedor |
| `application` | `core` | infra concreta, framework web, ORM |
| `infrastructure` | `core`, libs de provedor | `application` (salvo composition root) |
| `presentation` | `application` (via composição), contratos de I/O | regras de negócio, ORM direto, `core` “só desta vez” para furar o use case |

O **composition root** (DI) é o único lugar que instancia adaptadores concretos e os injeta nas portas. Fora dele, `new PostgresOrderRepo()` no use case é vazamento.

Anti-corruption: sistemas externos (WMS, ERP, Stripe) **nunca** vazam nomes/IDs para o domínio. O adaptador traduz. O domínio fala a língua do domínio.

UI (React, etc.) **não é domínio**. Fala com o produto por HTTP/contratos. Zero import de código de `core`/`application` do backend no frontend — e o inverso.

Limites entre bounded contexts: **sem import de implementação**. Contrato (HTTP, evento, pacote `contracts/`) ou nada.

Enforce: `import-linter` (Python), `eslint-plugin-boundaries` / `dependency-cruiser` (TS), testes estruturais no CI. Se o CI não barra o vazamento, o vazamento existe.

### Organização de repositório

Produto novo — **um bounded context por deployável**, não um monólito de pastas que se importam:

```
<repo>/
  AGENTS.md                 # este arquivo, ou o local que o estende
  docs/plans/               # só planos de trabalho em curso
  src/
    core/
      domain/
      ports/
    application/
    infrastructure/
      adapters/
      di/                   # composition root
    presentation/           # ou api/ + runtimes/
  tests/
    unit/                   # core + application, sem I/O
    contract/               # adaptador obedece a porta
    integration/
    e2e/
  deploy/                   # Dockerfiles, compose, charts
  .github/workflows/
```

Frontend: `apps/<nome>/` (ou repositório irmão). Integração = HTTP e contratos versionados.

Monorepo só quando os artefatos **nascem e versionam juntos**. Mesmo assim: nenhum import de código entre serviços. Compose na raiz; cada serviço permanece executável sozinho.

Não criar pacote `shared/` que vira lixeira. O que é compartilhado ou é contrato publicado ou não é compartilhado.

---

## 4. Stack canônica (produto novo)

Escolha **uma** coluna e seja hexagonal nela. Não misture Django-views-com-regra e FastAPI no mesmo bounded context.

| Peça | Canônico (Python) | Alternativa (TypeScript nativo) |
|------|-------------------|----------------------------------|
| Linguagem | Python 3.12 | TypeScript strict (`strict: true`) |
| API | FastAPI | NestJS (domínio **fora** dos controllers) |
| Tipos | Pydantic v2 | Zod na borda; tipos de domínio no `core` |
| DB | PostgreSQL 16 + **RLS** | PostgreSQL 16 + RLS |
| Migrações | Alembic | Prisma migrate **ou** SQL versionado — um dono, nunca dois |
| Cache / fila | Redis | Redis |
| HTTP client | porta + adaptador | porta + adaptador |
| Testes | pytest, asyncio strict | vitest / node:test |
| Lint / types | ruff + mypy | eslint + `tsc --noEmit` |
| Fronteiras | import-linter | dependency-cruiser |
| Frontend | React + Vite + TS | o mesmo |
| SSR | só se o requisito for SEO/first paint | Next.js somente então (YAGNI) |
| IaC local | Docker Compose | Docker Compose |
| CI | GitHub Actions | GitHub Actions |

**Frontend não calcula regra de negócio.** Pode validar UX (campo vazio, máscara). Autorização, preço, tenant, estoque: servidor.

**Não** para código novo, salvo legado inescapável: regra em stored procedure *e* no serviço; Server Action do Next como único backend sem `core`; ORM no controller; `any` / `dict` atravessando o domínio.

Comandos canônicos na raiz (`Makefile` é SSOT de *como rodar*):

```
make setup | lint | typecheck | test | build | up | down
```

CI chama os mesmos alvos. Ninguém documenta um comando que o Makefile não tem.

---

## 5. Analisar antes — as doze dimensões

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
| 8 | Segurança | Tenant do contexto? Authz no servidor? Input na borda? Segredo fora? Falha fechada? |
| 9 | Performance | Hot path? N+1? I/O no loop? Paginação? Índice? Timeout em todo I/O? |
| 10 | Escala / desacoplamento | Estado no processo? Gargalo é CPU, I/O ou fila? Cabe worker antes de outro serviço? |
| 11 | Resiliência | Worker morre no meio — o que acontece? Restart, DLQ, drain, idempotência? |
| 12 | Operação | Log sem PII, métrica, rollback, probe de vivo vs pronto, dono da flag? |

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
| Idempotência do worker (2ª entrega) | `tests/unit` do use case, relógio/fila mockados |
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
- **Tenant do contexto**, nunca do body/query escolhido pelo cliente.
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

Retry sem jitter e sem teto é amplificador de outage. “Vamos deixar o k8s reiniciar” **sem** idempotência é duplicar cobrança, e-mail, side-effect.

O domínio não conhece Kafka/Redis/Celery. A **porta** é `Queue` / `WorkerHeartbeat`. Auto-recovery é infra; a **correção** do reprocessamento é regra de application/core (idempotência).

### 8.4 Performance

- Sem N+1. Lista em batch. Coleção sem paginação = achado.
- Sem I/O síncrono no loop. Pool de conexões com teto; nunca conexão por request “no feeling”.
- Índice nasce com a query.
- Payload enxuto. Não serializar o agregado inteiro “por se acaso”.
- Medir o hot path (trace) antes de “otimizar” o que não dói.

### 8.5 Robustez e elegância

- Falha explícita (tipo / erro de domínio). `except: pass` e `None` silencioso são violação.
- Sem catch-all que engole e segue. Ou trata, ou propaga.
- Logs estruturados, sem PII, com `tenant_id` / `request_id` / `message_id`.
- Nomes que dizem a regra (`deny_if_other_tenant`, não `check`).
- Concorrência **limitada** (semáforo, `prefetch`, pool). “Unbounded gather” não é elegância.
- Diff pequeno, comportamento **completo**. Não metade do use case para commitar cedo.

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
        ├─ refatorar (limites SRP, DRY, camadas, resiliência)
        │
        ├─ make lint && make test
        │
        └─ não abrir PR / não mergear / não documentar extra
```

Não invente skill, pasta, ADR ou diagrama “para completar”. Skills de auditoria (`/principios-audit`, `/security-audit`) quando o humano pedir varredura — não a cada diff.

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

Qualquer um desses: pare, volte às dimensões, corrija o plano. Não empurre o diff.

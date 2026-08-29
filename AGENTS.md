# Constituição de desenvolvimento

Este arquivo é a **fonte única da verdade** de como se constrói software aqui. Vale para qualquer agente, IDE, CLI ou pessoa. Regras de um repositório específico (limites de bounded context, IDs de domínio, comandos) entram no `AGENTS.md` daquele repo e **prevalecem no que for local**. Este documento prevalece no que for princípio, processo e forma.

Código e prosa de produto: **português brasileiro**. Identificadores, APIs públicas e termos de mercado: inglês quando for o idioma do contrato.

---

## 0. Como usar este arquivo

Antes de implementar, o agente **lê esta constituição** e responde, em silêncio, às dez dimensões da §5. Se alguma dimensão falha, não se escreve código — escreve-se o plano ou pergunta-se.

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
10. **Segurança, desempenho e escala são requisitos**, não “depois”. Isolamento de tenant, auth no servidor, queries no limite, I/O explícito.

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

Proibido neste turno, salvo o humano pedir: feature flag morta, “base genérica para outros provedores”, microserviço novo para uma tela, event bus para um único consumidor, abstraction para um único implementador.

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

## 5. Analisar antes — as dez dimensões

Toda mudança, por menor que seja, passa por isto **antes** do primeiro teste. Se a mudança não for trivial (mais de um arquivo, contrato, ou comportamento), o resultado vira plano em `docs/plans/<slug>.md`.

| # | Dimensão | Pergunta |
|---|----------|----------|
| 1 | Correção | Qual invariante precisa continuar verdadeira? |
| 2 | SSOT | Onde esta regra já vive? Vou criar um segundo dono? |
| 3 | SRP | Esta unidade ganha um segundo motivo para mudar? |
| 4 | Hexagonal | Em que camada isso mora? Que porta existe ou falta? |
| 5 | DRY | Isto já está escrito? É decisão ou mapeamento? |
| 6 | YAGNI/KISS | O requisito de *agora* exige esta abstração? |
| 7 | TDD | Qual teste vai falhar primeiro, e o que ele prova? |
| 8 | Segurança | Tenant, authz no servidor, input, segredo, IDOR? |
| 9 | Performance/escala | Hot path? N+1? I/O no loop? Paginação? Idempotência? |
| 10 | Operação | Log, métrica, falha, rollback, feature flag com dono? |

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
| perf | ...
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
| Adaptador obedece porta | `tests/contract` |
| SQL, fila, HTTP real | `tests/integration` |
| Jornada | `tests/e2e` — poucos, estáveis |

CI: unit + contract + lint + fronteiras **sempre**. Integration/e2e no pipeline que tem a infra. Coverage é piso, não objetivo; cobertura de **comportamento** importa mais que % de linha.

---

## 7. Docker, CI/CD

### Docker

- Multi-stage. Imagem final mínima, **non-root**, sem toolchain, sem `.git`, sem `.env`.
- `HEALTHCHECK` ou probe equivalente.
- Compose: um serviço = um processo. Segredos só por env/secret, nunca `environment: PASSWORD=...` commitado.
- Mesma imagem em dev/CI/prod; o que muda é config.
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

## 8. Performance, escala, segurança, solidez

Não são fases. São o mesmo diff.

**Performance / escala**

- Sem N+1. Lista em batch. Paginação obrigatória em coleção.
- Sem I/O síncrono no loop. Sem query no domínio.
- Timeout, retry com jitter, idempotência em escrita e em consumidor.
- Índice nasce com a query, não “quando doer”.
- Trabalho pesado: fila + worker, não o request HTTP.

**Segurança**

- Isolamento de tenant no servidor (RLS e/ou filtro do contexto autenticado — SSOT do isolamento).
- Autorização no handler/use case, não só na UI.
- IDOR: todo get/mutate por ID verifica posse.
- Segredo fora do git; default `${VAR:-secret}` é segredo.
- Input na borda; HTML/e-mail escapados.
- Auditoria de segurança: skill `security-audit`.

**Solidez / elegância**

- Falha explícita (tipo, erro de domínio), não `None` silencioso.
- Logs estruturados, sem PII.
- Nomes que dizem a regra (`deny_if_other_tenant`, não `check`).
- Diff pequeno, comportamento completo. Não “metade do use case para commitar cedo”.

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
        ├─ refatorar (limites SRP, DRY, camadas)
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
- Novo microserviço, bus ou “plataforma” sem requisito
- Markdown novo fora de `docs/plans/` sem o humano pedir
- Commit com segredo, dump, `.env`, fixture com PII
- “É só um if” no lugar errado da camada

Qualquer um desses: pare, volte às dimensões, corrija o plano. Não empurre o diff.

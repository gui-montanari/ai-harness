# Sete categorias — procedimentos

Leia esta referência no Passo 0, depois execute cada categoria na ordem. Adapte os equivalentes à stack detectada.

## 1. ISOLAMENTO DE DADOS (inquilino/dono)

**Pergunta primeiro:** qual é o mecanismo de isolamento deste projeto?

| Stack | Equivalente |
|-------|-------------|
| Supabase / Postgres com RLS | Policies RLS em cada tabela exposta. Ausência = achado. |
| API própria (Nest, Django, Rails, FastAPI, Express…) | Toda listagem, busca, agregação, relatório e exportação **filtra** pelo usuário autenticado ou pela org/workspace/tenant dele. |
| Hasura / PostgREST | Permissions por role + filtros de tenant. |
| Prisma/Drizzle/SQLAlchemy/query builder | `where` de tenant em **todas** as queries de leitura agregada, não só no `findById`. |
| Mongo / Firebase | Regras de segurança ou filtro `tenantId` no servidor. |

O que procurar:

- `from('…').select()` / `findMany()` / `Model.all` / `SELECT` sem `user_id`/`org_id`/`tenant_id`/`workspace_id`
- Relatórios, CSV, dashboards, busca global, autocomplete, “admin stats”
- Endpoints que recebem `userId`/`orgId` do cliente e confiam nele
- RLS: tabela no schema público sem policy, ou policy `USING (true)`, ou só para `authenticated` sem checar `auth.uid()`
- Middleware de tenant que não roda em algumas rotas (webhooks, jobs, rotas “internas”, GraphQL resolvers soltos)

Aponte **onde o mecanismo está ausente ou furado**, não apenas que “falta RLS” de forma genérica.

Isolamento é **uma política global** (constituição §8.6): contexto autenticado + RLS `FORCE` (ou session `SET`) + posse no core. Handlers, workers, jobs e exports **herdam**. Achado extra quando:

- cada query copia `WHERE tenant_id =` com lógica **divergente** (segundo dono)
- o worker/job roda **sem** restaurar o contexto de tenant da mensagem
- o cliente manda `tenantId`/`orgId` e o servidor confia
- RLS existe mas **não** é `FORCE` (a app pode “esquecer” o filtro)

O mecanismo correto **substitui** a cópia. Não peça para adicionar o 41º `if tenant` — peça para o handler herdar o dono.

## 2. AUTORIZAÇÃO NO SERVIDOR

Toda operação possui policy deny-by-default por ação, objeto e campos retornados/alterados.
Sessão válida e tenant correto são pré-condições, não autorização suficiente. Inclua impedimento,
segregação de funções e four-eyes quando o domínio exigir.

Procedimento:

1. Inventarie ações sensíveis (`list`, `read`, `assign`, `resolve`, `export`, `reidentify`, admin).
2. Encontre gates de papel no frontend e ligue cada um ao endpoint correspondente.
3. Confirme policy no servidor por ação/objeto/campo; middleware de sessão sozinho não conta.
4. Confirme que actor/reviewer vêm do principal autenticado, nunca do body.
5. Teste papéis insuficientes, objeto impedido, campo protegido e autoaprovação.

Achado quando qualquer sessão autenticada executa a ação, quando a UI é o único gate ou quando
`actor_id`/`reviewer_id` do cliente satisfaz auditoria/four-eyes.

Se não houver frontend, declare N/A. Se o frontend e a API forem o mesmo processo (Server Actions / Inertia), ainda assim a checagem tem que estar no handler de servidor, não só no JSX.

## 3. IDOR E SUPERFÍCIES PÚBLICAS

Rotas que buscam, alteram ou deletam um objeto **por ID** (path, query ou body) sem verificar se o objeto pertence ao usuário/tenant do chamador.

**Percorra TODOS os handlers de rota do backend, não amostras.**

Inventário mínimo (grave em `docs/security-audit/coverage.md`):

```
arquivo:linha  método  rota/handler  objeto  checagem de posse  status
```

Status: `protegido` | `furado` | `publico-intencional` | `N/A`.

`publico-intencional` só é válido com requisito/ADR aceito citado como `arquivo:linha` no
`evidence.json`. Documentação auxiliar, teste existente ou rota já implementada não autorizam
a superfície. Verifique também personificação: cliente público não escolhe `sender_key`, tenant,
actor ou identidade técnica para acessar histórico/segredo.

O que é IDOR aqui:

- `GET /orders/:id`, `PATCH /users/:id`, `DELETE /files/:id`
- Body `{ "id": "…" }` / query `?reportId=`
- IDs previsíveis (inteiro sequencial) **e** UUIDs (UUID não é autorização)
- Downloads, exports, signed URLs, webhooks que aceitam ID de recurso
- GraphQL `node(id:)` / queries por PK
- Server Actions que recebem `id` do client

Não é IDOR se o handler carrega o recurso **e** compara `resource.tenantId === auth.tenantId` (ou equivalente) **antes** de ler/escrever/devolver.

## 4. AUTH E SESSÃO

Leia `auth`. Verifique cada emissor e superfície:

- sessão interna: MFA/SSO conforme requisito, cookie `HttpOnly; Secure; SameSite`, CSRF em
  mutações, expiração absoluta/inatividade, rotação, revogação e offboarding;
- SPA não armazena bearer de sessão em `localStorage`/`sessionStorage`;
- token público: alta entropia + hash, rate limit e miss uniforme; primeira troca cria sessão
  curta e redireciona para URL limpa;
- capability token não permanece em path/query, history, referrer, analytics ou log;
- JWT valida `iss`, `aud`, `exp`, algoritmo e scopes; público, interno e M2M não compartilham
  audience/cookie;
- webhook valida assinatura/body cru e replay conforme o provider.

## 5. SEGREDOS E DADOS SENSÍVEIS

API keys, tokens, senhas, segredos de assinatura (JWT, webhooks), chaves privadas, credenciais padrão embutidos em:

- código-fonte
- configs (`.env.example` com valor real, `application.yml`, `appsettings.json`)
- `docker-compose`, Helm charts, Terraform, CI (GitHub Actions, GitLab CI)
- scripts e documentação
- **defaults públicos** que viram segredo real se não forem sobrescritos: `${VAR:-valor-default}`, `os.getenv("X", "secret")`, `|| 'changeme'`
- ausência de validação de **startup** que rejeite esses defaults
- **histórico git** (`git log -p`, `git rev-list --all` + busca por `AKIA`, `sk-`, `-----BEGIN`, `api_key`, `SECRET`, `password`)
- **bundle do frontend** (`.env` com `NEXT_PUBLIC_`/`VITE_` contendo segredo de servidor; keys no JS minificado)

Segredo de cliente público (ex.: chave Stripe *publishable*, anon key Supabase) só é achado se estiver sendo usado como se fosse service role / secret key, ou se o repo tratar a anon key como confidencial sem necessidade — nesse caso: `informativa`.

Service role, JWT secret, webhook secret, private key, senha de banco → `critica` ou `alta` conforme produção vs. placeholder óbvio (`changeme` em compose de dev = `media`/`baixa` se o README manda trocar **e** o startup recusa o default; se o default sobe em prod, `alta`/`critica`).

Também nesta categoria (e em isolamento de dados quando o valor cruza tenant):

- `REDIS_URL` / `RABBITMQ_URL` vazias que sobem o processo; adapter tem de recusar no construtor.
- Valor de cache ou payload de evento com PII, token, relato, telefone.
- Chave de cache sem tenant (`t:{tenant}:…`).
- URL do host interpolada no compose de forma que o container aponte para `127.0.0.1` (não é segredo, mas é config que fura o isolamento do ambiente).
- identidade de canal, relato, contato, credencial ou token persistido em claro sem decisão de
  classificação, segregação/cifragem e retenção;
- PII em log, trace, métrica, URL, cache, evento, DLQ, fixture ou envelope bruto além do prazo;
- endpoint que devolve segredo/capability junto de histórico ou dado escolhido pelo cliente.

## 6. INPUTS E INJEÇÃO

**Frontend**

- `innerHTML`, `dangerouslySetInnerHTML`, `v-html`, `[innerHTML]`, equivalentes
- markdown/HTML renderizado sem sanitização
- URLs controladas por usuário em `href`/`src` (`javascript:`, `data:text/html`)
- `eval`, `new Function`, `setTimeout(string)`
- `document.write`

**Backend**

- input do usuário entrando em HTML de e-mails, templates (Jinja, ERB, Handlebars) ou respostas **sem escape**
- PDF/HTML gerado a partir de input
- Conteúdo que o frontend depois pinta como HTML
- SQL/command/template construído por concatenação de input
- URL fornecida pelo usuário sem allowlist de scheme/host/IP (SSRF)
- path/key de storage montado pelo cliente (path traversal)
- JSON/body sem schema, limites ou `additionalProperties` fechado quando o contrato é estreito

Verifique se existe lib de sanitização no projeto (`DOMPurify`, `sanitize-html`, `nh3`, `bleach`, auto-escape do template) **e se ela é aplicada nos pontos encontrados**. Ter a lib no `package.json` sem uso não mitiga o achado.

Se não houver frontend nem templates HTML, declare a metade correspondente N/A.

## 7. ABUSO E DISPONIBILIDADE

Segurança inclui impedir que uma entrada barata consuma recursos ilimitados:

- login, tracking, webhook e operações públicas com rate limit por chave apropriada e resposta
  uniforme; proteção contra enumeração e replay;
- listas sempre paginadas e com teto; busca/export com limites;
- tamanho de body/upload/mensagem e duração de áudio limitados na borda;
- timeout em toda saída; concorrência limitada por recurso; fila/buffer com teto;
- operações caras/idempotentes protegidas contra repetição e fan-out arbitrário;
- erro não devolve stack, segredo ou conteúdo confidencial.

Teste ao menos limite excedido, repetição/replay e coleção grande. “Volume atual é pequeno” não
mitiga endpoint público ou fila operacional sem teto.

# Cinco categorias — procedimentos

Leia esta referência no Passo 0, depois execute cada categoria na ordem. Adapte os equivalentes à stack detectada.

## 1. BANCO SEM TRANCA (isolamento de inquilino/dono)

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

## 2. PERMISSÃO DEFINIDA NO NAVEGADOR

Operações privilegiadas (admin, configurações, gestão de usuários, escritas perigosas) em que o **frontend esconde a UI** por papel (`isAdmin`, `canEdit`, `role`, `permissions`, feature flag de role) mas o **servidor não faz a verificação equivalente**.

Procedimento:

1. Encontre todos os gates de papel no frontend (`isAdmin`, `hasRole`, `can('…')`, `v-if="user.role"`, `if (!admin) return null`, rotas protegidas só no router do SPA).
2. Para cada gate, identifique o endpoint correspondente (mutate, action, REST, tRPC, Server Action, GraphQL mutation).
3. Confirme se o backend valida o privilégio **nessa rota**. Middleware global não conta se a rota está fora dele.

Achado quando: a UI some para o usuário comum, mas um POST/PATCH/DELETE autenticado (sem o papel) ainda executa.

Se não houver frontend, declare N/A. Se o frontend e a API forem o mesmo processo (Server Actions / Inertia), ainda assim a checagem tem que estar no handler de servidor, não só no JSX.

## 3. IDOR

Rotas que buscam, alteram ou deletam um objeto **por ID** (path, query ou body) sem verificar se o objeto pertence ao usuário/tenant do chamador.

**Percorra TODOS os handlers de rota do backend, não amostras.**

Inventário mínimo (grave em `docs/security-audit/coverage.md`):

```
arquivo:linha  método  rota/handler  objeto  checagem de posse  status
```

Status: `protegido` | `furado` | `publico-intencional` | `N/A`.

O que é IDOR aqui:

- `GET /orders/:id`, `PATCH /users/:id`, `DELETE /files/:id`
- Body `{ "id": "…" }` / query `?reportId=`
- IDs previsíveis (inteiro sequencial) **e** UUIDs (UUID não é autorização)
- Downloads, exports, signed URLs, webhooks que aceitam ID de recurso
- GraphQL `node(id:)` / queries por PK
- Server Actions que recebem `id` do client

Não é IDOR se o handler carrega o recurso **e** compara `resource.tenantId === auth.tenantId` (ou equivalente) **antes** de ler/escrever/devolver.

## 4. CHAVES EXPOSTAS (hardcode)

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

## 5. INPUTS SEM TRATAMENTO (XSS)

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

Verifique se existe lib de sanitização no projeto (`DOMPurify`, `sanitize-html`, `nh3`, `bleach`, auto-escape do template) **e se ela é aplicada nos pontos encontrados**. Ter a lib no `package.json` sem uso não mitiga o achado.

Se não houver frontend nem templates HTML, declare a metade correspondente N/A.

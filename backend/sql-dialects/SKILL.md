---
name: sql-dialects
description: >
  Use when integrating a relational SGBD, writing SQLAlchemy/Prisma that must
  run on more than one engine, switching Postgres and SQL Server via DATABASE_URL,
  or when the code uses JSONB, ON CONFLICT, RETURNING, UNIQUEIDENTIFIER, MERGE,
  mssql, asyncpg, or a dialect if in a repository. Ports and RLS: persistence-ports.
  Filenames: sql-migrations.
---

# Dialeto SQL no adapter

Trocar Postgres por SQL Server (ou o inverso) é **mudar a DSN**. Domínio, use case e porto **não** mudam. O composition root lê o scheme da URL e cria o engine.

**REQUIRED BACKGROUND:** `AGENTS.md` §3 e §8.6. Porto e RLS: `persistence-ports`. Nome de migration: `sql-migrations`.

Segundo dialeto **só com requisito real** (cliente, fonte, ambiente). Sem isso: um engine, mas **sem vazar** JSONB/`RETURNING`/`ON CONFLICT` para o modelo compartilhado — isso é o custo de um rewrite, não YAGNI.

## Interruptor

Uma factory. A URL escolhe o driver:

| DSN | Engine |
|-----|--------|
| `postgresql+asyncpg://…` | Postgres async |
| `mssql+aioodbc://…` | SQL Server async |

Pool, `pool_pre_ping`, `pool_recycle`, `statement_timeout` nascem **nessa** factory — API, worker e job herdam. Sync (`psycopg2`, `pyodbc`) no caminho async é achado.

```python
GUID = PG_UUID(as_uuid=False).with_variant(sa.String(36), "mssql")
```

Coluna de documento: `sa.JSON`, nunca `postgresql.JSONB`. Lista: `TypeDecorator` em texto. `DateTime(timezone=True)`. Boolean via `sa.Boolean` (o compilador traduz).

## SQL que muda de dialeto

Mora no adapter, atrás de um helper. Use case chama `repo.upsert(...)`.

| Operação | Postgres | SQL Server |
|----------|----------|------------|
| Upsert | `ON CONFLICT … DO UPDATE` | `MERGE` ou `UPDATE` + `INSERT` se `rowcount=0` |
| Insert ignore | `ON CONFLICT DO NOTHING` | `IF NOT EXISTS` / unique catch |
| Paginação | `LIMIT`/`OFFSET` | `OFFSET … FETCH` |
| Returning | `RETURNING` | `OUTPUT INSERTED` |
| Schema | `"name"` | `[name]` |

Migration **um** arquivo: `if bind.dialect.name == "postgresql":` / `"mssql"`. Dois runners = segundo dono (`sql-migrations`).

## Isolamento

RLS `FORCE` é backstop **Postgres**. Outro engine: equivalente de sessão (RLS do SQL Server, `SESSION_CONTEXT`) **e** o mesmo `assert_same_tenant` no core. Sem backstop = isolamento só na aplicação — achado.

## Teste

- Unit do use case: `Memory*` — zero SQL.
- Contract do repositório: a porta, contra o engine do requisito.
- Dois engines no requisito: os **dois** no CI (container). Um só: ainda assim o modelo usa tipos portáteis; o teste de contract não importa `asyncpg` no `core`.

## Red flags

- `if dialect` no use case, no domínio ou no handler HTTP
- `postgresql.JSONB` / `ARRAY` no metadata compartilhado
- SQL cru com `RETURNING` ou `LIMIT` copiado em três repositórios
- Adapter `SqlServer*` vazio “para o futuro”
- Trocar o dialeto exigindo diff em `application/` ou `core/`
- Factory de engine copiada na API e no worker

## Conferência

Antes de declarar pronto, copie e marque. Caixa vazia = falta.

- [ ] Uma factory; DSN escolhe o driver
- [ ] Tipos portáteis (`UUID.with_variant`, `sa.JSON`); sem JSONB no metadata compartilhado
- [ ] Upsert/`RETURNING` no adapter, não no use case
- [ ] Segundo dialeto só com requisito real
- [ ] Pool/timeout da factory herdados por API e worker
- [ ] Isolamento: RLS ou equivalente de sessão + `assert_same_tenant`

---
name: sql-migrations
description: >
  Use when adding or changing a database schema, SQL migration, Alembic/Prisma
  revision, docker-entrypoint dump, 001_init.sql, or when the user mentions
  YYYYMMDD_VV, schema_migrations, or too many migration files in one day.
---

# Migrations SQL

**REQUIRED BACKGROUND:** constituição `AGENTS.md` §3.2. O filename e o ledger são SSOT.

Um runner. Forward-only. Sem dump, sem `001_init.sql`, sem `docker-entrypoint-initdb.d`.

## Nome

```text
YYYYMMDD_VV__snake_description.sql
```

Regex: `^[0-9]{8}_[0-9]{2}__[a-z0-9_]+(\.sql|\.py)$`

Ordem = lexicográfica do filename.

## Mesmo dia: acrescente, não multiplique

Alvo: **um arquivo por dia de trabalho**.

| Situação | Ação |
|----------|------|
| Hoje já existe `YYYYMMDD_01__…sql` e **ainda não** está no ledger de ambiente compartilhado (não foi para main/staging/prod) | Abra esse arquivo e acrescente o `ALTER`/`CREATE`. Ajuste o `__snake_description` se o nome ficar mentiroso |
| Já aplicada / já no main | Novo `YYYYMMDD_02__…` (ou dia seguinte `_01`) |
| Breaking em produção | Sempre arquivo novo; nunca reeditar o que o ledger já viu |

Não crie `_02`, `_03`, `_04` no mesmo PR porque “cada ALTER merece um arquivo”. Volume alto no mesmo dia é achado.

## Conteúdo

- Idempotente na medida do dialeto (`IF NOT EXISTS`, ledger no-op).
- Sem senha, token, PII.
- RLS + `tenant_id` nascem com a tabela tenant-scoped.
- Role de app não é owner; sem `BYPASSRLS` em request/worker.
- Destrutiva: outro deploy, depois que o último leitor sumiu.

## Red flags

- `001_init.sql`, dump no entrypoint, `psql < schema.sql` no Makefile
- Dois runners (Alembic **e** SQL cru) no mesmo schema
- Dez arquivos `20260830_0N` no mesmo dia
- Editar migration já aplicada
- `CREATE TABLE` sem `tenant_id`/RLS em dado de negócio

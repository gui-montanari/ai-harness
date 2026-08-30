---
name: persistence-ports
description: >
  Use when adding a database, repository, ORM, RLS, tenant isolation in
  SQL, or when a graph/route/use case would import SQLAlchemy, Prisma,
  asyncpg, or a provider SDK. Redis cache: cache-ports. Blob: object-storage.
  Event bus: reliable-messaging.
---

# Persistência por porta

O banco é um **adapter**. Grafo LangGraph, rota HTTP e MCP **não** importam o driver. Use case fala com `OrderRepository` / `ObjectStoragePort`.

**REQUIRED BACKGROUND:** `AGENTS.md` §3 e §8.6 (RLS, tenant no contexto).

## Mapa

| Peça | Onde |
|------|------|
| Porto | `core/ports/` — `async`, sem SQL |
| Record | `infrastructure/adapters/` — ORM/row |
| Mapper | adapter (mecânico) |
| Migration | skill `sql-migrations` |
| Dialeto (Postgres ↔ SQL Server) | skill `sql-dialects` — a DSN escolhe o engine |
| Conexão, pool, RLS | composition root + sessão da request/worker |

Dois bounded contexts = dois schemas/roles. Mesmo cluster Postgres **não** autoriza JOIN cross-service. Processo composto (vários módulos no mesmo artefato) **não** unifica schema: cada porta usa o pool da role do dono (`AGENTS_DATABASE_URL` → `agents.*`).

## Regras

- Todo I/O de persistência é **async**.
- Tenant: sessão já nasce no tenant (`SET` / RLS `FORCE`). Esquecer `WHERE tenant_id` não pode vazar — o backstop é RLS + teste negativo.
- Role de app: sem `BYPASSRLS`, sem owner.
- Grafo / tool / MCP: recebem o porto já autenticado no tenant. Nunca `get_engine()`.
- Blob: skill `object-storage`. Fila/eventos: `reliable-messaging`. Cache: `cache-ports`.
- Trocar SGBD sem tocar `core/`/`application/`: skill `sql-dialects`.

## Red flags

- `asyncpg.connect` no use case ou no `graph.py`
- `service_role` / `BYPASSRLS` em request
- Tabela tenant-scoped sem RLS
- Dois serviços escrevendo a mesma tabela
- SDK Supabase em `core/`
- DSN com prefixo da marca ou do artefato (`TENDA_PG_*`, `WORKSPACE_DATABASE_URL`)
- Um `DATABASE_URL` só para um processo que hospeda vários donos
- Schema `workspace` / `platform` com tabelas de agents e cases
- Adapter de persistência lendo `os.environ` (a URL entra pelo composition root)
- `create_pool(..., max_size=10)` cravado; o teto é `DB_POOL_MAX_SIZE` na composição

## Conferência

Antes de declarar pronto, copie e marque. Caixa vazia = falta.

- [ ] Porto em `core/ports/`; record/mapper no adapter
- [ ] Use case e grafo sem SQLAlchemy/SDK
- [ ] I/O async; sessão já no tenant; RLS + teste negativo
- [ ] Role de app sem `BYPASSRLS` / owner
- [ ] Dialeto pela DSN (`sql-dialects`); blob = `object-storage`; cache = `cache-ports`
- [ ] Um DSN e um schema por dono; composition injeta o pool; adapter sem `getenv`

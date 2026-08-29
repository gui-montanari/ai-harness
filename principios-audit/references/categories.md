# Sete categorias — como varrer

A definição do princípio está no `AGENTS.md`. Aqui: **o que abrir e o que conta como achado**. Use o `inventory.json` como fila.

## 1. SSOT

Procure o mesmo fato em dois lugares:

- Fórmula, status machine, preço, desconto, timeout, tamanho de página
- Filtro de tenant no handler **e** de novo no repo **com lógica diferente**
- Campo com dois nomes sem anti-corruption (`accountId` no domínio lendo `stockfyClienteId` cru)
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

---
name: principios-audit
license: MIT
description: >
  Use when the user asks to audit architecture or design principles, check hexagonal
  layers, SSOT, SRP, DRY, YAGNI, KISS, SOLID, TDD, dead code, duplicated logic,
  file size limits, import leaks, worker auto-recovery, DLQ, decoupling, microservices,
  scalability, performance, architectural security, async-only, multi-tenant isolation,
  semaphore, retry policy, or idempotency (global policy inherited, not copied).
  Also when they run /principios-audit, /hexagonal-audit, or say "varredura de princípios".
---

# Auditoria de princípios (varredura completa)

Audite o repositório **contra a constituição**. SSOT das regras: `AGENTS.md` do projeto; se não houver, o template desta coleção (`../AGENTS.md`). Este skill é o **procedimento**. Não reescreva os princípios aqui.

Entregue achados verificados no código, inventário de cobertura, PDF em pt-BR e issues prontas.

## Checklist (copie e marque)

```
- [ ] 0. Ler AGENTS.md (projeto ou template) e detectar a stack/camadas reais
- [ ] 1. Rodar shared/scan_inventory.py — inventário, não amostragem
- [ ] 2. SSOT — dois donos da mesma regra
- [ ] 3. DRY — lógica duplicada (não mapeamento mecânico)
- [ ] 4. SRP — limites de linhas + “e” na responsabilidade
- [ ] 5. Hexagonal / DIP — vazamento de camada, composition root, anti-corruption
- [ ] 6. TDD — comportamento sem teste; teste que não falharia
- [ ] 7. Código morto — unused, flags mortas, trechos comentados
- [ ] 8. YAGNI / KISS — abstração sem segundo cliente; overengineering
- [ ] 9. Segurança arquitetural — falha fechada, tenant, authz, timeout, segredo (exploits profundos: /security-audit)
- [ ] 10. Escala / desacoplamento — worker vs microsserviço, estado, backpressure, dados
- [ ] 11. Resiliência — restart, ACK, DLQ, drain, probes
- [ ] 12. Runtime — async-only; tenant/retry/semáforo/idempotência **globais** (o resto herda)
- [ ] 13. Registrar o que está CORRETO (cobertura por camada)
- [ ] 14. findings.json + PDF + rasterizar páginas
- [ ] 15. Entregar no chat: arquivo:linha + caminhos
```

Não feche sem o inventário do scanner **e** sem o PDF verificado.

## Regras de ouro

1. **Constituição manda.** Limites de linha, camadas e TDD saem do `AGENTS.md` lido no passo 0. Se o repo local for mais estrito, use o local.
2. **Só achado no código real.** `arquivo:linha` + trecho. Scanner aponta suspeita; você confirma.
3. **Varredura, não amostra.** Todo arquivo de código do inventário entra: violação, protegido ou N/A.
4. **Categoria que não se aplica:** declare (ex.: repo só de Terraform — TDD de domínio N/A; infra ainda vale DRY/SRP).
5. **Não reescreva o sistema no relatório.** Achado + correção mínima. Refatoração heroica só se o humano pedir.

## Desculpas que não valem

| Desculpa | Realidade |
|----------|-----------|
| “Olhei os módulos principais” | O scanner listou N arquivos. Faltou 1? A cobertura está incompleta. |
| “O arquivo tem 280 linhas mas está organizado” | Domínio duro = 250. Extraia por responsabilidade. |
| “A regra no front é só UX” | Se calcula preço/tenant/estoque, é segundo dono (SSOT). |
| “core importa sqlalchemy só no type hint” | Vazamento. O porto não conhece o ORM. |
| “Não há testes porque o módulo é novo” | TDD exige o vermelho *antes*. É achado. |
| “Código comentado é documentação” | É morto. Apaga. |
| “Utils é o SSOT” | `utils`/`helpers` com regra de negócio é SRP + SSOT furados. |
| “O k8s já reinicia” | Restart sem idempotência duplica side-effect. É achado de resiliência. |
| “Dois serviços no mesmo banco é desacoplado” | É o pior acoplamento. Escala falsa. |
| “Segurança é a outra skill” | Exploits profundos são `/security-audit`. Falha aberta, tenant no body, timeout ausente entram **aqui**. |
| “Cada handler filtra tenant, está seguro” | Filtro copiado é segundo dono. Isolamento é contexto/RLS **global**. |
| “É só um requests.get no async” | Bloqueia o loop. Async-only. |
| “Retry no use case é mais claro” | Retry é política global. Use case não tem `for _ in range`. |

## Passo 0 — Constituição e stack

1. Leia `AGENTS.md` na raiz do projeto auditado. Se não existir, leia `<SKILL_DIR>/../AGENTS.md`.
2. Detecte: linguagem, framework, pastas de camada (`core`/`domain`, `application`, `infrastructure`/`adapters`, `presentation`/`api`, `tests`).
3. Mapeie as 11 categorias para **esta** árvore (pastas, compose, workers, filas, políticas globais). Grave em `docs/principios-audit/stack.md`.
4. Procedimento fino: [references/categories.md](references/categories.md).

## Passo 1 — Inventário (obrigatório)

```bash
python3 <SKILL_DIR>/../shared/scan_inventory.py . > docs/principios-audit/inventory.json
```

O JSON lista todos os arquivos de código, camada inferida, linhas vs limite, funções/classes estouradas, imports de infra em `core`/`application`, clusters de duplicação textual, `deploy.signals` (restart, healthcheck, probes, API+worker no mesmo command) e `runtime_smells` (`time.sleep`, `requests`, `readFileSync`, `gather(*)`).

**O scanner não fecha a auditoria.** Ele impede amostragem. Cada `over_file`, `functions_over`, `infra_imports`, cluster de `duplicates` e `deploy.signals` vira: achado confirmado, falso positivo documentado, ou N/A.

Percorra `inventory.json` **por completo**. Marque em `docs/principios-audit/coverage.md`:

```
arquivo  camada  linhas  SRP  hexagonal  dry/ssot  tdd  morto  segurança  escala  resiliência  runtime  status
```

status: `ok` | `achado` | `n/a`.

## Achado — formato

Grave em `docs/principios-audit/findings.json`. Schema: [references/findings-schema.md](references/findings-schema.md).

Categorias (`category`): `ssot` | `dry` | `srp` | `hexagonal` | `tdd` | `dead_code` | `yagni_kiss` | `security` | `scalability` | `resilience` | `runtime`

Severidade:

| Nível | Quando |
|-------|--------|
| `critica` | `core` depende de infra; regra de dinheiro/tenant/auth em dois donos; escrita de negócio sem teste; worker de cobrança sem idempotência; dois serviços escrevendo a mesma tabela |
| `alta` | vazamento de camada; arquivo ≥ 2× o limite; duplicação de regra; módulo novo sem unit; fila sem DLQ/ACK invertido; API e worker no mesmo processo com estado na RAM; falha aberta / tenant no body; I/O sync no event loop; retry/idempotência copiados no use case |
| `media` | arquivo acima do duro; função > 50; restart ausente; timeout ausente; liveness acoplada ao Redis; microsserviço sem o critério da constituição; `gather` sem semáforo |
| `baixa` | cheiro de tamanho; código comentado; helper genérico; probe único para vivo e pronto |
| `informativa` | fronteira ainda sem import-linter; dívida declarada no plano |

## Passo 14 — PDF

Obrigatório: `docs/principios-audit/relatorio-auditoria-principios.pdf`.

```bash
mkdir -p docs/principios-audit
cp <SKILL_DIR>/../shared/generate_report.py docs/principios-audit/
cp <SKILL_DIR>/../shared/requirements.txt docs/principios-audit/
cd docs/principios-audit
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python generate_report.py findings.json
```

Nunca pip global. Não reimplemente o layout. `report`, `category_labels` e `category_order` no JSON (veja o schema).

Verifique:

```bash
pdftoppm -png -r 150 relatorio-auditoria-principios.pdf /tmp/prin-page
pdfinfo relatorio-auditoria-principios.pdf
```

Corrija defeito visual e regenere.

## Passo 15 — Entrega no chat

1. Constituição usada (path) e camadas detectadas.
2. Números do inventário: arquivos, estouro de limite, leaks, clusters duplicados.
3. Achados **arquivo por arquivo, linha por linha**.
4. Pontos fortes (cobertura).
5. Caminhos: PDF, `findings.json`, `inventory.json`, `coverage.md`, `stack.md`.
6. Quantas issues no PDF.

Não abra issues no GitHub a menos que o humano peça.

## Red flags — PARE

- Achado sem `arquivo:linha`
- “Módulos principais” em vez de inventário
- Relatório que recita SOLID sem trecho
- Categoria omitida em silêncio
- PDF sem rasterizar
- Sugerir reescrever o monorepo inteiro no lugar de achados priorizados

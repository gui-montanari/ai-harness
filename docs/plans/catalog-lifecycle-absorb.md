# Plano: absorver mecanismos do pack agent-skills

Data: 2026-09-15
Status: feito

## Contexto

O pack addyosmani/agent-skills organiza HOW por fase do SDLC. O ai-harness
organiza HOW por capacidade de produto. Não copiamos o pack. Absorvemos
mecanismo (evals, anatomia, entrevista, fan-out de entrega) nos donos
atuais, sem skill nova.

## Invariantes

- Constituição continua SSOT de princípio; skill continua HOW; rule continua gate.
- Sem segundo catálogo SDLC, sem SPEC.md, sem CONSTRAINTS.md, sem commit automático.
- Pontes continuam curtas e só redirecionam.
- Kit Gate 2 continua o único roteador de skill (não nasce using-agent-skills).

## Dimensões

| Dimensão | Veredito | Nota |
| correção | ok | Catálogo ensina o mesmo HOW, com menos atalho |
| ssot | ok | Um dono por fato; evals não reescrevem a skill |
| srp | ok | eval_catalog.py só mede o catálogo |
| hexagonal | ok | N/A produto |
| dry | ok | Anatomia não copia a constituição |
| yagni | ok | Sem skill nova; Tier 3 comportamental fica de fora |
| tdd | ok | Fixture do eval falha antes do parser |
| segurança | ok | Sem segredo; evals são texto |
| performance | ok | TF-IDF no catálogo (~30 docs) |
| escala | ok | N/A |
| resiliência | ok | CLI exit ≠ 0 no vermelho |
| operação | ok | unittest no mesmo padrão do repo |
| runtime | ok | N/A produto |
| consistência | ok | name=pasta; headings em pt-BR |
| completude vertical | ok | pedido → kit → skill → conferência → eval |

## Abordagem

Uma: enriquecer donos. Evals = subset mecânico do skills-audit (não substitui o audit humano).

## Camadas e arquivos

| Arquivo | Camada | O que muda |
|---------|--------|------------|
| `quality/skills-audit/eval_catalog.py` | harness | parser, anatomia, roteamento, colisão |
| `quality/skills-audit/test_eval_catalog.py` | harness | TDD do eval |
| `quality/skills-audit/evals/cases.json` | harness | prompts positivos/negativos |
| `quality/skills-audit/SKILL.md` | HOW | passo mecânico + anatomia |
| `rules/analyze-before-implement.md` | gate | assumptions + entrevista + escopo |
| `rules/complete-until-done.md` | gate | browser isolado |
| `rules/ask-before-contract.md` | gate | expand/contract, advisory/compulsory |
| `rules/debug-hypotheses.md` | gate | stop-the-line |
| skills de execução | HOW | Quando não usar + Desculpas |
| `architecture/SKILL.md` | HOW | fan-out, review 5 eixos, medir primeiro |
| demais skills/constituição | HOW | conteúdo absorvido no dono |

## Contratos

Nenhum contrato publicado de produto. Catálogo interno do harness.

## Testes (RED primeiro)

- [ ] `quality/skills-audit/test_eval_catalog.py` — parser, anatomia, rank, colisão, cases cobrem execução
- [ ] unittest das pastas já existentes continua verde

## Fora de escopo

- Skill `using-agent-skills`, `interview-me`, `SPEC.md`, feature flags
- Evals comportamentais (Tier 3, gasta token)
- Comandos slash `/spec` `/ship` (WHEN) — o gate já dispara
- Persona-roteadora

## Critérios de aceite

- [ ] Execução tem Quando não usar + Desculpas; ponte não
- [ ] `python3 -m unittest quality.skills-audit.test_eval_catalog` não existe como módulo — rodar no diretório da skill
- [ ] Rank-1 dos cases positivos; negativos não vencem o owner
- [ ] Gate 1 entrevista; architecture gate com fan-out e rollback
- [ ] skills-audit do diff: zero bloqueante/material do que esta mudança introduziu

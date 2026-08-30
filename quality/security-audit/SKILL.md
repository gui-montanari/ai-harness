---
name: security-audit
license: MIT
description: >
  Use when the user asks to audit application security, review code for security
  flaws, check IDOR, RLS, tenant isolation, XSS, hardcoded secrets, client-side-only
  authorization, broken access control, or generate a security audit PDF. Also when
  they run /security-audit, /auditoria-seguranca, or say "revisa este código atrás
  de falhas de segurança". Produces a verified pt-BR PDF report and GitHub-ready issues.
---

# Auditoria de segurança (5 categorias)

Audite o repositório atual em cinco categorias, **adaptadas à stack real**. Reporte só o que o código prova. Entregue achados no chat, um PDF em pt-BR e issues prontas para colar no GitHub.

## Checklist (copie e marque)

```
- [ ] 0. Detectar a stack e o mecanismo de isolamento
- [ ] 1. BANCO SEM TRANCA — isolamento de inquilino/dono
- [ ] 2. PERMISSÃO DEFINIDA NO NAVEGADOR — gate de papel só no frontend
- [ ] 3. IDOR — TODOS os handlers de rota (não amostras)
- [ ] 4. CHAVES EXPOSTAS — código, configs, git history, bundle frontend; REDIS_URL/RABBITMQ_URL fail-closed; cache/evento sem PII
- [ ] 5. INPUTS SEM TRATAMENTO (XSS) — frontend e backend
- [ ] 6. Registrar o que está CORRETO (cobertura)
- [ ] 7. Gerar findings.json + PDF + verificar páginas
- [ ] 8. Entregar no chat: achados linha a linha + caminhos dos arquivos
```

Não pule etapa. Não feche a auditoria sem o PDF verificado.

## Regras de ouro

1. **Só achado verificado no código real.** Sem especulação, sem “talvez”, sem CVE genérico da stack.
2. **Arquivo por arquivo, linha por linha.** Cada achado: caminho, número(s) exato(s) da linha, trecho, por que é explorável, severidade (`critica` | `alta` | `media` | `baixa` | `informativa`).
3. **O que está correto também entra.** Ex.: “router X valida posse em todos os handlers”. Isso vira a seção de pontos fortes e **prova a cobertura**.
4. **Categoria que não se aplica à stack:** declare explicitamente (ex.: “sem frontend — categoria 2 e 5 frontend N/A”) em vez de forçar achado.
5. **Anote condições de explorabilidade** (feature flag, config insegura necessária, ambiente, autenticação prévia, etc.).
6. **IDOR não é amostragem.** Percorra sistematicamente **todos** os handlers de rota do backend. Se o conjunto for grande, inventarie-os (arquivo:handler) e marque cada um: protegido / furado / N/A.

## Desculpas que não valem

| Desculpa | Realidade |
|----------|-----------|
| “Revisei as rotas principais” | IDOR exige **todas**. Inventário completo. |
| “Provavelmente tem RLS no banco” | Se não está no repo (migration, policy, middleware), está ausente. |
| “O frontend esconde o botão” | Sem checagem no servidor, é achado da categoria 2. |
| “É só um default de desenvolvimento” | `${VAR:-segredo}` commitado vira segredo real. |
| “Não gerei o PDF porque o relatório no chat basta” | O PDF é entregável obrigatório. |
| “Instalei reportlab no sistema” | Use venv isolado. Nunca pip global. |
| “A categoria não se aplica, então omiti” | Declare N/A com a razão. |

## Passo 0 — Detectar a stack

Antes de qualquer categoria, identifique e registre:

- linguagem(ns)
- framework web
- ORM / query builder
- mecanismo de auth (JWT, session, cookies, Supabase Auth, NextAuth, etc.)
- frontend (se houver) e como fala com a API
- deploy: Docker, CI, Helm, Terraform, compose, charts
- **mecanismo de isolamento de tenant/dono** (tem de ser **global**, o resto herda): RLS FORCE / session SET / middleware que cobre HTTP **e** worker; não um `if` copiado por rota. Ver constituição §8.6.

Mapeie cada categoria para o equivalente dessa stack. Escreva o mapeamento em `docs/security-audit/stack.md` (vai para a capa do PDF).

Detalhe por categoria: leia [references/categories.md](references/categories.md) agora e siga os procedimentos de cada uma.

## Achado — formato canônico

Grave cada achado em `docs/security-audit/findings.json` (schema em [references/findings-schema.md](references/findings-schema.md)). Campos mínimos:

- `id`, `category`, `severity`, `file`, `lines`, `title`
- `description`, `snippet`, `why_exploitable`
- `exploitability_conditions`, `impact`, `fix`, `acceptance_criteria`

Severidade:

| Nível | Quando |
|-------|--------|
| `critica` | Acesso cross-tenant a dados, RCE, segredo de produção commitado, bypass total de auth |
| `alta` | IDOR em objeto sensível, admin sem checagem no servidor, XSS armazenado |
| `media` | IDOR em objeto de baixo impacto, default inseguro, XSS refletido |
| `baixa` | Info leak limitado, sanitização incompleta, segredo de dev |
| `informativa` | Superfície, config duvidosa sem exploração comprovada |

## Passo 6 — Cobertura (pontos fortes)

Além dos achados, registre o que foi verificado e está correto. Exemplos válidos:

- “`src/routes/orders.ts` valida posse (`order.userId === ctx.user.id`) em GET/PATCH/DELETE”
- “Policies RLS em `supabase/migrations/00xx_orders.sql` cobrem SELECT/INSERT/UPDATE/DELETE de `orders`”
- “Não há `dangerouslySetInnerHTML` / `v-html` / `innerHTML` no frontend”

Isso não é elogio genérico. É evidência de que a categoria foi percorrida.

## Passo 7 — Relatório PDF

Obrigatório: `docs/security-audit/relatorio-auditoria-seguranca.pdf`.

1. Escreva `docs/security-audit/findings.json` completo.
2. Copie o gerador desta skill para o projeto auditado:

```bash
mkdir -p docs/security-audit
cp <SKILL_DIR>/../../shared/generate_report.py docs/security-audit/
cp <SKILL_DIR>/../../shared/requirements.txt docs/security-audit/
```

`SKILL_DIR` é a pasta desta skill (onde está este `SKILL.md`). O gerador vive em `shared/` (SSOT das duas auditorias).

3. Gere o PDF **em venv isolado** (nunca pip global):

```bash
cd docs/security-audit
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python generate_report.py findings.json
```

O script valida o JSON, desenha os gráficos e escreve o PDF. Não reimplemente o layout.

4. Conteúdo exigido do PDF (o gerador cobre a forma; você preenche os dados): capa, resumo executivo com rosca + barras, pontos fortes/fracos, tabela de achados, recomendações P1/P2/P3…, seção final **ISSUES PARA O GITHUB**. Detalhe em [references/report-and-issues.md](references/report-and-issues.md).

5. **Verifique o PDF antes de entregar.** Rasterize:

```bash
pdftoppm -png -r 150 relatorio-auditoria-seguranca.pdf /tmp/audit-page
pdfinfo relatorio-auditoria-seguranca.pdf
```

Abra as PNGs. Corrija sobreposição, tabela cortada, gráfico ilegível, header/footer faltando — regenere. Só então declare pronto.

Paleta (já no gerador): crítica `#B91C1C`, alta `#EA580C`, média `#D97706`, baixa `#2563EB`, ponto forte `#059669`, informativa `#6B7280`.

## Passo 8 — Entrega no chat

Nesta ordem:

1. Stack detectada e mapeamento das 5 categorias.
2. Lista de achados **arquivo por arquivo, linha por linha** (com severidade).
3. Pontos fortes (cobertura).
4. Caminho do PDF e de todos os arquivos gerados (`findings.json`, `stack.md`, `generate_report.py`, venv local, PNG de verificação se houver).
5. Quantas issues foram agrupadas para o GitHub (o texto completo delas vive no PDF).

Não abra as issues no GitHub a menos que o usuário peça.

## Red flags — PARE

- Achado sem `arquivo:linha` e sem trecho
- “Rotas típicas” em vez de inventário de handlers
- Categoria omitida em silêncio
- pip / npm / cargo install global para gerar o PDF
- PDF sem gráficos, sem issues, ou sem página de capa
- PDF não rasterizado

## Conferência

A checklist do topo **é** a conferência desta skill. Todas as caixas marcadas + PDF rasterizado antes de entregar.

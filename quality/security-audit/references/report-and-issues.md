# Relatório PDF e issues GitHub

O gerador `scripts/generate_report.py` produz `relatorio-auditoria-seguranca.pdf` a partir de `findings.json`. Não recrie o layout. Preencha o JSON.

## Seções do PDF (nessa ordem)

a) **Capa** — título `Relatório de Auditoria de Segurança — <nome do projeto>`, data, escopo, nota metodológica (mapeamento das 7 categorias para a stack).

b) **Resumo executivo** — totais por severidade, gráfico de rosca por severidade, gráfico de barras por categoria. Paleta: crítica `#B91C1C`, alta `#EA580C`, média `#D97706`, baixa `#2563EB`, ponto forte `#059669`.

c) **Pontos fortes e pontos fracos** — o que está protegido (com evidência) e os riscos centrais.

d) **Tabela de achados** — Severidade | Arquivo:linha | Descrição, com chip colorido.

e) **Recomendações priorizadas** — P1, P2, P3…

f) **ISSUES PARA O GITHUB** — para cada issue acionável, o texto COMPLETO em Markdown, pronto para copiar e colar, entre:

```
--- ISSUE n ---
# [Segurança] ...
...
--- FIM ISSUE n ---
```

## Regras técnicas de geração

- Não instalar nada globalmente. Venv Python com `reportlab` + `matplotlib` (veja `scripts/requirements.txt`).
- Deixar o script gerador em `docs/security-audit/` do **projeto auditado** para regenerar depois.
- Verificar o PDF: número de páginas, gráficos, tabelas. Rasterizar (`pdftoppm`) e corrigir defeitos visuais.
- Páginas A4, margens ~2 cm, cabeçalho/rodapé com nome do relatório e número de página.

## Template de issue (corpo)

```markdown
## Problema

<o que está errado e por que é explorável>

## Evidência

`<arquivo>:<linhas>`

```<lang>
<trecho>
```

## Impacto

<o que um atacante obtém>

## Sugestão de correção

<mudança concreta>

## Critérios de aceite

- [ ] <verificável 1>
- [ ] <verificável 2>
- [ ] Teste automatizado cobre o caso

Labels sugeridas: `security`, `<severidade>`
```

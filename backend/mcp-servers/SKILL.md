---
name: mcp-servers
description: >
  Use when exposing a product to Grok, Cursor, ChatGPT or any MCP host, adding
  a custom connector, Streamable HTTP MCP, or when the user mentions MCP
  server, grok.com/connectors, or remote MCP. For each tool, catalog, profile,
  or exposing an agent journey: mcp-tools.
---

# Servidor MCP

MCP é **outra borda** do mesmo produto, não um segundo backend. O processo, o transporte e a descoberta vivem aqui. O que entra em `tools/list`: skill `mcp-tools`.

**REQUIRED SUB-SKILL:** `http-apis` (contrato HTTP), `mcp-tools` (cada tool), `auth` (quando o host exige login).

## Transporte

Para Grok / xAI remote MCP: **Streamable HTTP** (SSE legado só se o host exigir). URL **pública**. `localhost` é rejeitado — túnel só em dev.

Stateless. Sem sessão mágica no processo.

## Descoberta

`initialize` + `tools/list`. A lista deste processo = união dos **perfis** montados. Env só liga perfis já aprovados no código — não nomes soltos de tool. Conteúdo de cada tool: `mcp-tools`.

Host que pede `allowed_tools` deve poder restringir. Perfil no servidor **e** allowlist no host: os dois.

## Grok (norte de plataforma)

1. API de produto em `/api/v1` (skill `http-apis`).
2. Borda MCP em `/mcp` (Streamable HTTP) no **mesmo** composition root.
3. Se o host mandar request sem token: `401` + metadata OAuth (skill `auth`, emissor `connector`).
4. Admin cola a URL em grok.com/connectors → Custom.
5. Tools aparecem no host: OAuth uma vez, depois chamada sob demanda.

## Red flags

- Segundo backend “só para MCP”
- stdio como único transporte para conector na nuvem
- Segredo na query string `?token=`
- Env publicando nomes arbitrários de tool
- Composition root distinto da API

## Conferência

Antes de declarar pronto, copie e marque. Caixa vazia = falta.

- [ ] Streamable HTTP público; composition root o mesmo da API
- [ ] Auth do conector pela skill `auth` (PKCE se o host exigir)
- [ ] Este processo monta só perfis aprovados; env não inventa tool
- [ ] Conferência de `mcp-tools` marcada para cada tool/jornada deste servidor

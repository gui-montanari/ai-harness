---
name: mcp-servers
description: >
  Use when exposing a product to Grok, Cursor, ChatGPT or any MCP host, adding
  a custom connector, Streamable HTTP MCP, tool schemas, or when the user
  mentions MCP server, grok.com/connectors, or remote MCP tools.
---

# Servidor MCP

MCP é **outra borda** do mesmo produto, não um segundo backend. Tools chamam use cases. SQL, LLM e regra ficam onde já estavam.

**REQUIRED SUB-SKILL:** `http-apis` (contrato) e `oauth-connectors` (quando o host exige login).

## Transporte

Para Grok / xAI remote MCP: **Streamable HTTP** (SSE legado só se o host exigir). URL **pública**. `localhost` é rejeitado — túnel só em dev.

Stateless. Sem sessão mágica no processo.

## Tools

| Deve | Não deve |
|------|----------|
| Nome estável, verbo+objeto (`list_cases`) | `run_query`, `execute_sql` |
| `inputSchema` JSON Schema estreito | `additionalProperties: true` genérico |
| Chamar um use case | Abrir o banco |
| Authz do principal do conector | Confiar no host |
| Timeout e idempotência herdados | Retry local copiado |
| Texto sem PII no retorno | Relato integral, token, segredo |

Allowlist no manifest. Tool nova = contrato versionado. Host que pede `allowed_tools` deve poder restringir.

## Descoberta

`initialize` + `tools/list`. Descrição da tool é o contrato que o modelo lê: uma frase, parâmetros óbvios, o que **não** faz.

## Grok (norte de plataforma)

1. API de produto em `/api/v1` (skill `http-apis`).
2. Borda MCP em `/mcp` (Streamable HTTP) no **mesmo** composition root.
3. Se o host mandar request sem token: `401` + metadata OAuth (`oauth-connectors`).
4. Admin cola a URL em grok.com/connectors → Custom.
5. Tools aparecem no host: OAuth uma vez, depois chamada sob demanda.

## Red flags

- MCP que executa SQL / shell
- Duplicar o use case “porque é tool”
- stdio como único transporte para conector na nuvem
- Segredo na query string `?token=`
- Tool sem schema, sem timeout, sem tenant

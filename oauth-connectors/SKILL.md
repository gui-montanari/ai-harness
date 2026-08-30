---
name: oauth-connectors
description: >
  Use when adding OAuth for an LLM platform connector (Grok, ChatGPT, Claude),
  MCP Protected Resource, PKCE, authorization code, well-known metadata, or
  when a host returns 401 and must discover how to log the user in.
---

# OAuth de conector (LLM / MCP)

Dois OAuth distintos. Não misture.

| Fluxo | Grant | Quem | Skill |
|-------|-------|------|-------|
| API de produto M2M | `client_credentials` | serviço→serviço | `http-apis` |
| Conector no Grok/ChatGPT | **Authorization Code + PKCE S256** | humano autoriza o host | este |

O conector Stockfy no Grok funciona porque o host completa OAuth **uma vez** e depois chama tools com Bearer. Esse é o norte.

## O que o host (Grok) espera

1. MCP Streamable HTTP numa URL pública (`mcp-servers`).
2. Request sem token → `401` + `WWW-Authenticate: Bearer FAKESECRET_g3h4i5j6k7l8m9n0o1p2="https://<api>/.well-known/oauth-protected-resource"`.
3. RFC 9728: `/.well-known/oauth-protected-resource` (e o path da resource, se houver).
4. RFC 8414: `/.well-known/oauth-authorization-server` (`authorization_endpoint`, `token_endpoint`, `code_challenge_methods_supported: S256`, `scopes_supported`).
5. Autorização no browser: `response_type=code`, PKCE, `state`, `redirect_uri` **fixo do host** (allowlist).
6. `POST /oauth/token`: code + verifier → access token curto + refresh token.
7. Resource indicator / `audience` = a URL do MCP. Token de outro recurso não passa.

Dynamic Client Registration (RFC 7591) só se o host exigir. Senão, `client_id` estável documentado.

## Implementação (camadas)

- Endpoints OAuth = **apresentação**. Não guardam regra de caso.
- Tokens, clients, codes = adapter + domínio mínimo (`AuthorizationCode`, `RefreshToken`).
- PKCE S256 obrigatório. Implicit e senha no token endpoint: proibidos.
- Segredo de assinatura no secret manager, ≥32 bytes, sem default.
- Refresh rotaciona. Code de um uso, TTL minutos.
- Scope estreito (`mcp:tools`). Não reaproveitar o JWT interno do backoffice.

## Auth da API de produto (não é isto)

`client_credentials` + JWT interno, rate-limit de falhas, tenant no contexto: já está em `http-apis`. Widget/visitor token é outro principal. Não use o IdP do Grok para o colaborador da Tenda.

## Red flags

- Colar `client_secret` no MCP URL
- Redirect URI coringa
- Access token eterno
- Um JWT para backoffice **e** conector Grok
- Metadata `well-known` mentindo os endpoints
- Password grant “só para o Grok”

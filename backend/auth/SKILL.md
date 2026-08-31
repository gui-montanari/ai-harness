---
name: auth
description: >
  Use when adding or changing login, JWT, OAuth2, OIDC, SSO, MFA, session
  cookies, client_credentials, service-to-service tokens, webhook HMAC,
  visitor/public tokens, MCP connector OAuth, PKCE, or authorization of a
  principal. Replaces inventing a new auth flavor per surface.
---

# Auth

**REQUIRED BACKGROUND:** constituição `AGENTS.md` §8.1. Autenticação identifica; autorização (policy, deny-by-default) é outra casa, na application. Não misture as duas.

Um **principal de domínio**, imutável, invariantes na construção. Vários **emissores**. Não vários sistemas de login.

## Catálogo — não invente o sexto

| Necessidade | Mecanismo | `auth_source` |
|-------------|-----------|----------------|
| Humano interno | OIDC/SSO (candidato) ou sessão após MFA | `internal` |
| Serviço → serviço | OAuth2 `client_credentials` → JWT curto | `m2m` |
| Superfície pública limitada | token opaco de alta entropia, **hash** no banco | `public` — não é conta |
| Webhook de provider | HMAC/assinatura no **body cru**, antes de parsear | `provider` |
| Host MCP / LLM | Authorization Code + **PKCE S256** | `connector` |
| Nós chamamos outro serviço | `client_credentials` ou refresh **cifrado** em store | outbound |

Cada borda **traduz** para o mesmo `Principal` (`tenant_id`, `subject`, `scopes`, `auth_source`). Handler nunca lê claim crua. Tenant vem do token/sessão, nunca do body.

## JWT (interno e M2M)

- `iss`, `aud`, `exp`, `iat` obrigatórios. `algorithms` allowlist (nunca `alg=none`).
- HS256 só com um emissor e segredo no secret manager. Mais de um serviço verificando: RS256/ES256.
- Segredo ≥32 bytes, sem default. Rotação: atual + anterior.
- TTL curto (minutos a 1h). Scope estreito (`frozenset`).
- Rate-limit de falhas por `tenant + client_id`.
- Endpoint: `POST /oauth/token` com `grant_type=client_credentials`. Secret do client **hashed**. `sub` = `client_id`.

## Humano interno

`IdentityProviderPort` → claims → `Principal`. Cookie `HttpOnly`, `Secure`, `SameSite`; CSRF na mutação. Sessão interna **não** compartilha cookie, cache ou audience com a superfície pública. Offboarding revoga membership mesmo com claim ainda válida.

Sessão tem expiração absoluta e por inatividade, rotação após login/elevação e revogação
server-side. MFA/SSO segue o requisito da superfície interna. SPA não persiste Bearer em
`localStorage`/`sessionStorage`; prefira cookie HttpOnly ou BFF quando o browser for o cliente.

## Pública limitada

Não cria usuário. Hash + salt, rate-limit, resposta uniforme no miss, headers `no-store`. JWT público só com `iss`/`aud` **distintos** do interno.

O segredo pode chegar uma vez por link, mas a primeira resposta válida o troca por sessão
pública curta em cookie `HttpOnly; Secure; SameSite`, redireciona para URL limpa e permite
revogação. Não mantenha capability token em path/query, histórico, referrer, analytics ou log.

## Webhook

Assinatura sobre a representação original. Falha → 401, sem parse de negócio.

## Conector MCP / LLM

Host autoriza **uma vez**, depois Bearer.

1. Sem token → `401` + `WWW-Authenticate: Bearer FAKESECRET_g3h4i5j6k7l8m9n0o1p2="https://<api>/.well-known/oauth-protected-resource"`.
2. RFC 9728 e RFC 8414 (`S256` em `code_challenge_methods_supported`).
3. `redirect_uri` allowlist (URI fixo do host). Code de um uso, TTL minutos. Refresh rotaciona.
4. `audience` = URL do MCP. Token de outro `aud` não passa.
5. Scope `mcp:tools`. **Não** reutilizar o JWT interno.

DCR (RFC 7591) só se o host exigir. Implicit e password grant: proibidos.

## Outbound

Store de bearer cifrado, nunca em log, evento ou JSON de domínio. Refresh no adapter. Falha de refresh é erro tipado, não retry infinito.

## Camadas

```
core/domain/          Principal, AuthSource
core/ports/           IdentityProviderPort, TokenSigner, BearerTokenStore
infrastructure/adapters/auth/
presentation/http/v1/auth/   # token + well-known; sem regra de caso
```

## Red flags

- Quinto grant “só para este host”
- Um JWT / um cookie para público **e** interno
- `tenant_id` no body autorizando
- Secret na query string
- Capability token permanecendo na URL após a troca inicial
- Access token eterno; redirect URI coringa
- Bearer de sessão do browser em Web Storage; sessão sem expiração/revogação/rotação
- Policy só na UI
- `jwt.decode` sem `algorithms`, `iss`, `aud`
- Principal como dict solto entre camadas

## Conferência

Antes de declarar pronto, copie e marque. Caixa vazia = falta.

- [ ] Um `Principal` de domínio; emissor no catálogo (não um sexto grant)
- [ ] Tenant do token/sessão, nunca do body
- [ ] JWT: `iss`/`aud`/`exp`/`algorithms` allowlist
- [ ] Público e interno com cookie/audience distintos
- [ ] Sessão interna expira, rotaciona e revoga; browser não guarda Bearer em Web Storage
- [ ] Token público é trocado por sessão curta e a URL fica limpa; miss uniforme e rate-limited
- [ ] Webhook assina o body cru; MCP usa PKCE S256 se o host exigir
- [ ] Segredo fora de git, log e URL

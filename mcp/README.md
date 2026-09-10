# MCP da máquina

Catálogo agnóstico + adapters por host. Segredo **nunca** entra no git.

| Onde | O que |
|------|--------|
| `catalog/mcp-catalog.json` | Servidores universais |
| `secrets.example/*.env.example` | Contrato das chaves |
| `~/.config/ai-harness/secrets/*.env` | Valores reais (cópia local) |
| `~/.config/ai-harness/overlay/mcp/` | Servidores só desta máquina + `browser.env` (perfil Chrome do OAuth) |
| `~/.mcp-auth/` | Refresh token OAuth (Cloudflare, Make, Stripe) |

O `install.sh` da raiz copia exemplos de secret que ainda não existem, liga os wrappers em `~/bin` e sincroniza os hosts. Plugin Hostinger do Cursor: o `npx @latest` paralelo corria em `ENOTEMPTY` e shebang sem `+x`; o `sync` reescreve o `mcp.json` do plugin para `scripts/run-hostinger-plugin` + `node` local (`mcp_servers/hostinger`). Plugin 1Password: o Electron não acha `1password-mcp` no PATH (`ENOENT`); o `sync` aponta para `scripts/run-1password-mcp` (binário em `~/.local/opt/1Password` ou `/opt/1Password`).

Primeiro login OAuth é no browser do host (Cursor, Grok, Claude): Cloudflare, Make e Stripe usam **URL HTTP nativa**, sem `mcp-remote` — o host guarda o token. Mercado Pago continua em `mcp-remote` com header Bearer (não abre browser). Para o wrapper de Chrome do harness (quando ainda houver `mcp-remote` de overlay), `~/.config/ai-harness/overlay/mcp/browser.env` com `CHROME_PROFILE_DIRECTORY=` (pasta em `~/.config/google-chrome/`, ex. `Default`).

Para um MCP que não é universal (VPS, cliente): `~/.config/ai-harness/overlay/mcp/catalog.json` no formato de `overlay.example.json`.

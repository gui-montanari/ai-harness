# MCP da máquina

Catálogo agnóstico + adapters por host. Segredo **nunca** entra no git.

| Onde | O que |
|------|--------|
| `catalog/mcp-catalog.json` | Servidores universais |
| `secrets.example/*.env.example` | Contrato das chaves |
| `~/.config/ai-harness/secrets/*.env` | Valores reais (cópia local) |
| `~/.config/ai-harness/overlay/mcp/` | Servidores só desta máquina |
| `~/.mcp-auth/` | Refresh token OAuth (Cloudflare, Make, Stripe) |

O `install.sh` da raiz copia exemplos de secret que ainda não existem, liga os wrappers em `~/bin` e sincroniza os hosts. Primeiro login OAuth é no browser; os seguintes reusam o token.

Para um MCP que não é universal (VPS, cliente): `~/.config/ai-harness/overlay/mcp/catalog.json` no formato de `overlay.example.json`.

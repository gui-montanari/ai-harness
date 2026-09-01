# Telegram Docs MCP

Servidor MCP local e somente leitura para documentação oficial do Telegram.

Ele não usa token de bot, não autentica contas e não envia mensagens. Todas as
leituras de rede são limitadas a URLs HTTPS de `core.telegram.org`.

## Ferramentas

- `list_telegram_doc_sources`
- `search_telegram_docs`
- `fetch_telegram_doc`
- `get_telegram_bot_api_reference`

As páginas são mantidas em cache por seis horas em
`~/.cache/mcp-cli-toolkit/telegram-docs`. Se a documentação estiver
temporariamente indisponível, um cache anterior pode ser usado como fallback e a
resposta será marcada como `stale-cache`.

Variáveis opcionais:

```text
TELEGRAM_DOCS_CACHE_DIR
TELEGRAM_DOCS_CACHE_TTL_SECONDS
```

## Execução manual

```bash
python3 mcp_servers/telegram_docs/server.py
```

O processo usa JSON-RPC/MCP sobre STDIO e normalmente deve ser iniciado por um
dos wrappers do toolkit.

# Twilio MCP

MCP operacional oficial (`@twilio-alpha/mcp`) para chamar APIs da conta Twilio.
É separado do `twilio-docs`, que permanece somente documental e sem autenticação.

O servidor usa API Key (SID `SK` + secret) com Account SID (`AC`). Credenciais
ficam em `~/.config/ai-harness/secrets/twilio.env`; o wrapper não as
grava no catálogo nem na config dos clientes.

Por limite de contexto do modelo, o padrão carrega só o núcleo de conta,
mensagens, conteúdo e números. Amplie `TWILIO_SERVICES` no secret se precisar
de outras APIs.

O MCP executa chamadas reais na conta. Trate cada ferramenta como escrita
potencial: envio de SMS/WhatsApp, compra de número, alteração de recurso.

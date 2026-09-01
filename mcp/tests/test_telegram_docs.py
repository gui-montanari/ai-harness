import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


SERVER_PATH = Path(__file__).resolve().parents[1] / "mcp_servers/telegram_docs/server.py"
SPEC = importlib.util.spec_from_file_location("telegram_docs_server", SERVER_PATH)
server = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = server
SPEC.loader.exec_module(server)


SAMPLE_HTML = """
<!doctype html>
<html>
  <body>
    <h1><a name="bot-api">Telegram Bot API</a></h1>
    <p>This is the official Bot API reference.</p>
    <h4><a name="sendmessage">sendMessage</a></h4>
    <p>Use this method to send text messages.</p>
    <table>
      <tr><th>Parameter</th><th>Type</th></tr>
      <tr><td>chat_id</td><td>Integer or String</td></tr>
      <tr><td>text</td><td>String</td></tr>
    </table>
    <h4><a name="update">Update</a></h4>
    <p>This object represents an incoming update.</p>
  </body>
</html>
"""


def parsed_document():
    parser = server.TelegramDocsHTMLParser()
    parser.feed(SAMPLE_HTML)
    parser.close()
    return parser.parsed(
        url="https://core.telegram.org/bots/api",
        fetched_at=1_700_000_000,
        cache_state="test-cache",
    )


class TelegramDocsServerTest(unittest.TestCase):
    def test_initialize_and_tools_are_read_only(self):
        initialized = server._handle(
            {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {"protocolVersion": "2024-11-05"},
            }
        )
        self.assertEqual(initialized["result"]["serverInfo"]["name"], "telegram-docs")

        listed = server._handle({"jsonrpc": "2.0", "id": 2, "method": "tools/list"})
        self.assertEqual(
            [tool["name"] for tool in listed["result"]["tools"]],
            [
                "list_telegram_doc_sources",
                "search_telegram_docs",
                "fetch_telegram_doc",
                "get_telegram_bot_api_reference",
            ],
        )
        self.assertTrue(
            all(tool["annotations"]["readOnlyHint"] for tool in listed["result"]["tools"])
        )
        self.assertTrue(
            all(
                not tool["annotations"]["destructiveHint"]
                for tool in listed["result"]["tools"]
            )
        )

    def test_only_official_https_urls_are_accepted(self):
        self.assertEqual(
            server._validate_official_url("bot-api"),
            "https://core.telegram.org/bots/api",
        )
        self.assertEqual(
            server._validate_official_url("/bots/features"),
            "https://core.telegram.org/bots/features",
        )
        for unsafe in (
            "http://core.telegram.org/bots/api",
            "https://example.com/bots/api",
            "https://core.telegram.org.evil.example/bots/api",
            "https://user:password@core.telegram.org/bots/api",
        ):
            with self.subTest(unsafe=unsafe), self.assertRaises(ValueError):
                server._validate_official_url(unsafe)

    def test_redirect_handler_rejects_external_domains(self):
        handler = server.OfficialTelegramRedirectHandler()
        with self.assertRaises(ValueError):
            handler.redirect_request(
                mock.Mock(),
                mock.Mock(),
                302,
                "Found",
                {},
                "https://example.com/redirected",
            )

    def test_parser_preserves_bot_api_headings_and_tables(self):
        document = parsed_document()
        send_message = next(
            section for section in document.sections if section.title == "sendMessage"
        )
        self.assertEqual(send_message.anchor, "sendmessage")
        self.assertIn("chat_id", send_message.text)
        self.assertIn("Integer or String", send_message.text)

    @mock.patch.object(server, "_load_document")
    def test_exact_bot_api_reference_includes_official_anchor(self, load_document):
        load_document.return_value = parsed_document()

        result = server.bot_api_reference("sendMessage")

        self.assertIn("Use this method to send text messages", result)
        self.assertIn("https://core.telegram.org/bots/api#sendmessage", result)

    @mock.patch.object(server, "_load_document")
    def test_search_returns_matching_official_sections(self, load_document):
        load_document.return_value = parsed_document()

        result = server.search_documents(
            "incoming update",
            sources=["bot-api"],
            max_results=3,
        )

        self.assertIn("Update", result)
        self.assertIn("https://core.telegram.org/bots/api#update", result)

    def test_cache_falls_back_when_network_is_unavailable(self):
        with tempfile.TemporaryDirectory() as temporary:
            with mock.patch.dict(
                server.os.environ,
                {
                    "TELEGRAM_DOCS_CACHE_DIR": temporary,
                    "TELEGRAM_DOCS_CACHE_TTL_SECONDS": "300",
                },
                clear=False,
            ):
                server._write_cache(
                    "https://core.telegram.org/bots/api",
                    SAMPLE_HTML,
                    1_700_000_000,
                )
                with (
                    mock.patch.object(server, "_download", side_effect=OSError("offline")),
                    mock.patch.object(server.time, "time", return_value=1_800_000_000),
                ):
                    document = server._load_document("bot-api")

        self.assertEqual(document.cache_state, "stale-cache")
        self.assertTrue(document.sections)

    def test_tool_errors_are_returned_as_mcp_tool_results(self):
        response = server._handle(
            {
                "jsonrpc": "2.0",
                "id": 3,
                "method": "tools/call",
                "params": {
                    "name": "fetch_telegram_doc",
                    "arguments": {"path_or_url": "https://example.com"},
                },
            }
        )
        self.assertTrue(response["result"]["isError"])
        self.assertIn("core.telegram.org", response["result"]["content"][0]["text"])


if __name__ == "__main__":
    unittest.main()

from types import SimpleNamespace
from unittest.mock import Mock, patch

from django.test import SimpleTestCase, override_settings

from ai_features.services.claude import generate_text


class TestEmptyGenerationDiagnostics(SimpleTestCase):
    def setUp(self):
        self.response = SimpleNamespace(
            content=[SimpleNamespace(type="tool_use")],
            model="gateway-model",
            stop_reason="tool_use",
            usage=SimpleNamespace(output_tokens=12),
            id="response-123",
        )
        self.client = Mock()
        self.client.messages.create.return_value = self.response

    @override_settings(AI_CLAUDE_MODEL="requested-model", AI_FALLBACK_MODEL="")
    @patch("ai_features.services.claude.get_anthropic_client")
    def test_primary_empty_response_logs_metadata_without_prompt(self, get_client):
        get_client.return_value = self.client

        with self.assertLogs("ai_features.services.claude", level="WARNING") as logs:
            answer = generate_text("private system prompt", "private user question")

        self.assertEqual(answer, "")
        log_message = logs.output[0]
        self.assertIn("Primary generation returned no text", log_message)
        self.assertIn("requested_model=requested-model", log_message)
        self.assertIn("response_model=gateway-model", log_message)
        self.assertIn("stop_reason=tool_use", log_message)
        self.assertIn("content_block_types=['tool_use']", log_message)
        self.assertIn("output_tokens=12", log_message)
        self.assertIn("response_id=response-123", log_message)
        self.assertNotIn("private", log_message)

    @override_settings(AI_FALLBACK_MODEL="fallback-model")
    @patch("ai_features.services.claude.get_fallback_client")
    @patch("ai_features.services.claude.get_anthropic_client", return_value=None)
    def test_fallback_empty_response_logs_metadata(self, _primary_client, get_client):
        get_client.return_value = self.client

        with self.assertLogs("ai_features.services.claude", level="WARNING") as logs:
            answer = generate_text("system prompt", "user question")

        self.assertEqual(answer, "")
        self.assertTrue(any("Fallback generation returned no text" in line for line in logs.output))
        self.assertTrue(any("response_id=response-123" in line for line in logs.output))

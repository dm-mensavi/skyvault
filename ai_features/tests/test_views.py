import json
from types import SimpleNamespace
from unittest.mock import patch

from django.test import RequestFactory, SimpleTestCase

from ai_features.views import ask_vault


class TestAskVault(SimpleTestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def _post_query(self, query):
        request = self.factory.post(
            "/vault/ask/",
            data=json.dumps({"query": query}),
            content_type="application/json",
        )
        request.user = SimpleNamespace(is_authenticated=True)
        return request

    @patch("ai_features.views.generate_text", return_value="")
    @patch("ai_features.views.search_chunks", return_value=[])
    def test_empty_generation_returns_error_instead_of_greeting(self, _search, _generate):
        response = ask_vault(self._post_query("summarize the files in my drive"))

        self.assertEqual(response.status_code, 503)
        data = json.loads(response.content)
        self.assertIn("error", data)
        self.assertNotIn("answer", data)

    @patch("ai_features.views.generate_text", return_value="Hello! How can I help?")
    def test_chitchat_returns_generated_answer_with_reasoning_budget(self, generate):
        response = ask_vault(self._post_query("hey"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.content)["answer"], "Hello! How can I help?")
        generate.assert_called_once()
        self.assertEqual(generate.call_args.kwargs["max_tokens"], 1000)

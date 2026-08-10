"""
Retrieval / vector-search tests.

All tests run WITHOUT real OpenAI or Anthropic keys.
We patch 'ai_features.services.search.embed_text' (the name as imported in
search.py) so the real HTTP call is never made.  A deterministic zero-vector
is returned instead; pgvector still runs cosine-distance against it normally.
"""
from unittest.mock import patch
from django.test import TestCase
from django.contrib.auth.models import User


# ---------------------------------------------------------------------------
# Helper: the module-level name to patch is where search.py *imported* it.
# ---------------------------------------------------------------------------
EMBED_PATCH = "ai_features.services.search.embed_text"
ZERO_VEC = [0.0] * 384


class TestSearchChunks(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="testpass")

    @patch(EMBED_PATCH, return_value=[])
    def test_empty_query_returns_empty(self, _mock):
        from ai_features.services.search import search_chunks
        results = search_chunks(self.user, "", top_k=5)
        self.assertEqual(results, [])

    @patch(EMBED_PATCH, return_value=[])
    def test_whitespace_query_returns_empty(self, _mock):
        from ai_features.services.search import search_chunks
        results = search_chunks(self.user, "   ", top_k=5)
        self.assertEqual(results, [])

    @patch(EMBED_PATCH, return_value=ZERO_VEC)
    def test_user_isolation(self, _mock):
        """Results must never include another user's chunks."""
        from ai_features.services.search import search_chunks
        from vault.models import File, Folder

        other = User.objects.create_user(username="otheruser", password="x")
        folder = Folder.objects.create(user=other, name="folder")
        File.objects.create(user=other, folder=folder, name="other.pdf", size=100)

        results = search_chunks(self.user, "query", top_k=5)
        for chunk in results:
            self.assertEqual(chunk.file.user_id, self.user.id)


class TestSearchFiles(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(username="fileuser", password="testpass")

    def _make_file_with_chunks(self, name, n_chunks=2, trashed=False):
        from vault.models import File, Folder
        from ai_features.models import DocumentChunk, FileAnalysis

        folder = Folder.objects.create(user=self.user, name=f"folder_{name}")
        file_obj = File.objects.create(
            user=self.user, folder=folder, name=name, size=1000, trashed=trashed
        )
        analysis, _ = FileAnalysis.objects.get_or_create(
            file=file_obj, defaults={"status": FileAnalysis.Status.DONE, "extracted_text": "text"}
        )
        for i in range(n_chunks):
            DocumentChunk.objects.create(
                file=file_obj, analysis=analysis,
                chunk_index=i, content=f"chunk {i}", embedding=ZERO_VEC,
            )
        return file_obj

    @patch(EMBED_PATCH, return_value=ZERO_VEC)
    def test_deduplicates_by_file(self, _mock):
        from ai_features.services.search import search_files
        self._make_file_with_chunks("report.pdf", n_chunks=3)
        results = search_files(self.user, "query", top_k=10)
        file_names = [r["file"].name for r in results]
        self.assertEqual(file_names.count("report.pdf"), 1)

    @patch(EMBED_PATCH, return_value=ZERO_VEC)
    def test_excludes_trashed_files(self, _mock):
        from ai_features.services.search import search_files
        self._make_file_with_chunks("active.pdf", trashed=False)
        self._make_file_with_chunks("deleted.pdf", trashed=True)
        results = search_files(self.user, "query", top_k=10)
        file_names = [r["file"].name for r in results]
        self.assertIn("active.pdf", file_names)
        self.assertNotIn("deleted.pdf", file_names)

    @patch(EMBED_PATCH, return_value=ZERO_VEC)
    def test_result_has_score_field(self, _mock):
        from ai_features.services.search import search_files
        self._make_file_with_chunks("scored.pdf")
        results = search_files(self.user, "query", top_k=5)
        for r in results:
            self.assertIn("score", r)
            self.assertIsInstance(r["score"], float)

    @patch(EMBED_PATCH, return_value=ZERO_VEC)
    def test_empty_vault_returns_empty(self, _mock):
        from ai_features.services.search import search_files
        results = search_files(self.user, "query", top_k=5)
        self.assertEqual(results, [])
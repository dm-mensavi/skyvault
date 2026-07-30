from unittest.mock import patch
from django.test import TestCase, RequestFactory
from django.contrib.auth.models import User
from ai_features.services.search import search_chunks, search_files


class TestRetrieval(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="testpass")

    @patch("ai_features.services.embeddings.embed_text")
    def test_search_chunks_returns_empty_for_empty_query(self, mock_embed):
        mock_embed.return_value = [0.0] * 1536
        results = search_chunks(self.user, "", top_k=5)
        self.assertEqual(results, [])

    @patch("ai_features.services.embeddings.embed_text")
    def test_search_chunks_returns_empty_for_whitespace_query(self, mock_embed):
        mock_embed.return_value = [0.0] * 1536
        results = search_chunks(self.user, "   ", top_k=5)
        self.assertEqual(results, [])

    @patch("ai_features.services.embeddings.embed_text")
    def test_search_chunks_user_isolation(self, mock_embed):
        mock_embed.return_value = [0.0] * 1536
        other_user = User.objects.create_user(username="otheruser", password="testpass")

        from vault.models import File, Folder
        folder = Folder.objects.create(user=self.user, name="shared_folder")
        file_other = File.objects.create(
            user=other_user, folder=folder, name="other_doc.pdf", size=1000
        )

        results = search_chunks(self.user, "query", top_k=5)
        for chunk in results:
            self.assertEqual(chunk.file.user, self.user)

    @patch("ai_features.services.embeddings.embed_text")
    def test_search_files_deduplicates_by_file(self, mock_embed):
        mock_embed.return_value = [0.0] * 1536
        from ai_features.models import DocumentChunk, FileAnalysis
        from vault.models import File, Folder

        folder = Folder.objects.create(user=self.user, name="test_folder")
        file_obj = File.objects.create(
            user=self.user, folder=folder, name="report.pdf", size=5000
        )
        analysis = FileAnalysis.objects.create(
            file=file_obj, status=FileAnalysis.Status.DONE, extracted_text="test"
        )

        DocumentChunk.objects.create(
            file=file_obj,
            analysis=analysis,
            chunk_index=0,
            content="relevant content",
            embedding=[0.0] * 1536,
        )
        DocumentChunk.objects.create(
            file=file_obj,
            analysis=analysis,
            chunk_index=1,
            content="more relevant content",
            embedding=[0.0] * 1536,
        )

        results = search_files(self.user, "query", top_k=10)
        file_names = [r["file"].name for r in results]
        self.assertEqual(file_names.count("report.pdf"), 1)

    @patch("ai_features.services.embeddings.embed_text")
    def test_search_files_excludes_trashed(self, mock_embed):
        mock_embed.return_value = [0.0] * 1536
        from ai_features.models import DocumentChunk, FileAnalysis
        from vault.models import File, Folder

        folder = Folder.objects.create(user=self.user, name="trash_folder")
        trashed_file = File.objects.create(
            user=self.user, folder=folder, name="deleted.pdf", size=1000, trashed=True
        )
        active_file = File.objects.create(
            user=self.user, folder=folder, name="active.pdf", size=2000
        )
        analysis = FileAnalysis.objects.create(
            file=active_file, status=FileAnalysis.Status.DONE, extracted_text="active content"
        )
        analysis2 = FileAnalysis.objects.create(
            file=trashed_file, status=FileAnalysis.Status.DONE, extracted_text="deleted content"
        )

        DocumentChunk.objects.create(
            file=active_file, analysis=analysis, chunk_index=0,
            content="active chunk", embedding=[0.0] * 1536,
        )
        DocumentChunk.objects.create(
            file=trashed_file, analysis=analysis2, chunk_index=0,
            content="trashed chunk", embedding=[0.0] * 1536,
        )

        results = search_files(self.user, "query", top_k=10)
        file_names = [r["file"].name for r in results]
        self.assertNotIn("deleted.pdf", file_names)

    @patch("ai_features.services.embeddings.embed_text")
    def test_search_returns_relevance_score(self, mock_embed):
        mock_embed.return_value = [0.0] * 1536
        from ai_features.models import DocumentChunk, FileAnalysis
        from vault.models import File, Folder

        folder = Folder.objects.create(user=self.user, name="score_folder")
        file_obj = File.objects.create(
            user=self.user, folder=folder, name="scored.pdf", size=3000
        )
        analysis = FileAnalysis.objects.create(
            file=file_obj, status=FileAnalysis.Status.DONE, extracted_text="scored content"
        )
        DocumentChunk.objects.create(
            file=file_obj, analysis=analysis, chunk_index=0,
            content="score test content", embedding=[0.0] * 1536,
        )

        results = search_files(self.user, "query", top_k=5)
        for r in results:
            self.assertIn("score", r)
            self.assertIsInstance(r["score"], float)
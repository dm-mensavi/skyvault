import os
import tempfile
from unittest.mock import MagicMock, patch
from django.test import TestCase
from ai_features.extractors import extract_text
from ai_features.extractors.pdf import extract_pdf


class TestPDFExtractor(TestCase):

    @patch("pdfplumber.open")
    def test_extract_pdf_small_page_count(self, mock_pdf_open):
        """PDF with <= 10 pages extracts all pages."""
        pages = []
        for i in range(5):
            page = MagicMock()
            page.extract_text.return_value = f"Page content {i + 1}"
            pages.append(page)

        mock_pdf = MagicMock()
        mock_pdf.pages = pages
        mock_pdf_open.return_value.__enter__.return_value = mock_pdf

        result = extract_pdf("dummy.pdf")
        self.assertIsNotNone(result)
        self.assertIn("Page content 1", result)
        self.assertIn("Page content 5", result)
        self.assertEqual(len(result.split("\n\n")), 5)

    @patch("pdfplumber.open")
    def test_extract_pdf_large_page_count(self, mock_pdf_open):
        """PDF with > 10 pages extracts only first 5 and last 5 pages."""
        pages = []
        for i in range(15):
            page = MagicMock()
            page.extract_text.return_value = f"Page content {i + 1}"
            pages.append(page)

        mock_pdf = MagicMock()
        mock_pdf.pages = pages
        mock_pdf_open.return_value.__enter__.return_value = mock_pdf

        result = extract_pdf("large_document.pdf")
        self.assertIsNotNone(result)

        # First 5 pages (1..5) should be present
        for p in range(1, 6):
            self.assertIn(f"Page content {p}", result)

        # Middle pages (6..10) should NOT be present
        for p in range(6, 11):
            self.assertNotIn(f"Page content {p}", result)

        # Last 5 pages (11..15) should be present
        for p in range(11, 16):
            self.assertIn(f"Page content {p}", result)

    def test_unsupported_non_pdf_extension(self):
        with tempfile.NamedTemporaryFile(suffix=".bin", delete=False) as f:
            f.write(b"text data")
            temp_path = f.name

        try:
            result = extract_text(temp_path, "bin")
            self.assertIsNone(result)
        finally:
            os.unlink(temp_path)

    def test_missing_file(self):
        result = extract_text("/nonexistent/path/file.pdf", "pdf")
        self.assertIsNone(result)

import os
import tempfile
from django.test import TestCase
from ai_features.extractors import extract_text


class TestPlaintextExtractor(TestCase):

    def test_extract_plain_txt(self):
        content = "This is a test document.\nSecond line."
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False, mode="w", encoding="utf-8") as f:
            f.write(content)
            f.flush()
            temp_path = f.name

        try:
            result = extract_text(temp_path, "txt")
            self.assertIsNotNone(result)
            self.assertIn("test document", result)
        finally:
            os.unlink(temp_path)

    def test_extract_markdown(self):
        content = "# Heading\n\nSome **bold** text."
        with tempfile.NamedTemporaryFile(suffix=".md", delete=False, mode="w", encoding="utf-8") as f:
            f.write(content)
            f.flush()
            temp_path = f.name

        try:
            result = extract_text(temp_path, "md")
            self.assertIsNotNone(result)
            self.assertIn("Heading", result)
        finally:
            os.unlink(temp_path)

    def test_extract_with_latin1_encoding(self):
        content = "Café résumé naïve"
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False, mode="wb") as f:
            f.write(content.encode("latin-1"))
            f.flush()
            temp_path = f.name

        try:
            result = extract_text(temp_path, "txt")
            self.assertIsNotNone(result)
            self.assertIn("Café", result)
        finally:
            os.unlink(temp_path)

    def test_unsupported_extension(self):
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as f:
            f.write(b"fake image data")
            temp_path = f.name

        try:
            result = extract_text(temp_path, "jpg")
            self.assertIsNone(result)
        finally:
            os.unlink(temp_path)

    def test_missing_file(self):
        result = extract_text("/nonexistent/path/file.txt", "txt")
        self.assertIsNone(result)

    def test_empty_file(self):
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False, mode="w") as f:
            temp_path = f.name

        try:
            result = extract_text(temp_path, "txt")
            self.assertIsNotNone(result)
        finally:
            os.unlink(temp_path)

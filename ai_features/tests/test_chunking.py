from django.test import TestCase
from ai_features.chunking import chunk_text


class TestChunking(TestCase):

    def test_paragraph_split(self):
        text = "First paragraph.\n\nSecond paragraph.\n\nThird paragraph."
        chunks = chunk_text(text, max_chars=25)
        self.assertEqual(len(chunks), 3)
        self.assertEqual(chunks[0]["content"], "First paragraph.")
        self.assertEqual(chunks[1]["content"], "Second paragraph.")
        self.assertEqual(chunks[2]["content"], "Third paragraph.")

    def test_max_chunk_size_enforced(self):
        long_para = "word " * 600
        text = f"Short.\n\n{long_para}\n\nAnother short."
        chunks = chunk_text(text, max_chars=2000)
        for chunk in chunks:
            self.assertLessEqual(len(chunk["content"]), 2000)

    def test_overlap_preserved(self):
        text = "A.\n\nB.\n\nC."
        chunks = chunk_text(text, max_chars=2000, overlap_chars=100)
        self.assertGreater(len(chunks), 0)

    def test_min_chunk_merge(self):
        # First chunk is >50 chars, trailing chunk is <50 chars, merged together
        text = ("Long paragraph with enough text to exceed fifty characters easily."
                "\n\nTiny.")
        chunks = chunk_text(text, max_chars=2000, overlap_chars=0)
        self.assertEqual(len(chunks), 1)
        self.assertIn("Tiny", chunks[0]["content"])

    def test_empty_text(self):
        chunks = chunk_text("")
        self.assertEqual(len(chunks), 0)

    def test_whitespace_only_text(self):
        chunks = chunk_text("   \n\n  \n\n   ")
        self.assertEqual(len(chunks), 0)

    def test_chunk_index_sequential(self):
        text = "Para one.\n\nPara two.\n\nPara three."
        chunks = chunk_text(text, max_chars=25)
        for i, chunk in enumerate(chunks):
            self.assertEqual(chunk["chunk_index"], i)

    def test_token_count_approx(self):
        text = "word " * 100
        chunks = chunk_text(text)
        if chunks:
            approx_tokens = chunks[0]["token_count"]
            self.assertGreater(approx_tokens, 0)

    def test_single_long_paragraph_split(self):
        sentences = ". ".join(f"Sentence number {i} is here to add characters" for i in range(50))
        text = f"Intro.\n\n{sentences}\n\nConclusion."
        chunks = chunk_text(text, max_chars=500)
        self.assertGreater(len(chunks), 1)
        all_content = " ".join(c["content"] for c in chunks)
        self.assertIn("Intro", all_content)
        self.assertIn("Conclusion", all_content)
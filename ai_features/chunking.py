import logging
import re

logger = logging.getLogger(__name__)

DEFAULT_MAX_CHARS = 2000    # ~500 tokens
DEFAULT_OVERLAP_CHARS = 200 # ~50 tokens
MIN_CHUNK_CHARS = 50       # merge fragments smaller than this into previous chunk


def chunk_text(
    text: str,
    max_chars: int = DEFAULT_MAX_CHARS,
    overlap_chars: int = DEFAULT_OVERLAP_CHARS
) -> list[dict]:
    """
    Semantic Document Chunking Strategy:
    1. Primary split on double-newline paragraph boundaries (\\n\\n) to preserve narrative context.
    2. Enforces max_chars threshold per chunk with sliding overlap.
    3. Merges tiny trailing fragments (< 50 chars) to prevent vector noise.

    Why this strategy over fixed-size character splitting:
    Fixed-size naive splitting breaks sentences and code blocks in half, destroying semantically
    rich context needed for high-precision RAG vector retrieval. Paragraph splitting keeps
    coherent thoughts intact while overlap preserves boundary context.
    """
    if not text or not text.strip():
        return []

    # Clean multi-line whitespace
    clean = text.strip().replace("\r\n", "\n")
    paragraphs = [p.strip() for p in clean.split("\n\n") if p.strip()]

    raw_chunks = []
    current_chunk = ""

    for paragraph in paragraphs:
        if len(current_chunk) + len(paragraph) + 2 <= max_chars:
            current_chunk = f"{current_chunk}\n\n{paragraph}".strip() if current_chunk else paragraph
        else:
            if current_chunk:
                raw_chunks.append(current_chunk)

            # If a single paragraph is longer than max_chars, split on single newline or sentences
            if len(paragraph) > max_chars:
                sub_parts = re.split(r"(?<=[.!?])\s+", paragraph)
                sub_chunk = ""
                for part in sub_parts:
                    if len(sub_chunk) + len(part) + 1 <= max_chars:
                        sub_chunk = f"{sub_chunk} {part}".strip() if sub_chunk else part
                    else:
                        if sub_chunk:
                            raw_chunks.append(sub_chunk)
                        # Sliding overlap step
                        overlap = sub_chunk[-overlap_chars:] if len(sub_chunk) >= overlap_chars else sub_chunk
                        sub_chunk = f"{overlap} {part}".strip() if overlap else part
                if sub_chunk:
                    current_chunk = sub_chunk
            else:
                # Include sliding overlap from previous chunk
                overlap = current_chunk[-overlap_chars:] if len(current_chunk) >= overlap_chars else current_chunk
                current_chunk = f"{overlap}\n\n{paragraph}".strip() if overlap else paragraph

    if current_chunk:
        raw_chunks.append(current_chunk)

    # Post-process: merge tiny fragments (< MIN_CHUNK_CHARS) into preceding chunk
    final_chunks = []
    for chunk in raw_chunks:
        chunk_str = chunk.strip()
        if not chunk_str:
            continue
        if final_chunks and len(chunk_str) < MIN_CHUNK_CHARS:
            final_chunks[-1] += f"\n\n{chunk_str}"
        else:
            final_chunks.append(chunk_str)

    # Format structured dictionary response
    results = []
    for idx, content in enumerate(final_chunks):
        # Approximate token count (1 token ≈ 4 chars)
        approx_tokens = max(1, len(content) // 4)
        results.append({
            "chunk_index": idx,
            "content": content,
            "token_count": approx_tokens,
        })

    return results

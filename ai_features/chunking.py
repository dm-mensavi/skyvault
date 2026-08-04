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
    2. Sub-splits overlong paragraphs on sentence boundaries.
    3. Enforces max_chars threshold per chunk with sliding overlap.
    4. Merges tiny trailing fragments (< 50 chars) without violating max_chars.
    """
    if not text or not text.strip():
        return []

    clean = text.strip().replace("\r\n", "\n")
    paragraphs = [p.strip() for p in clean.split("\n\n") if p.strip()]
    if not paragraphs:
        return []

    # Step 1: Normalize paragraphs (sub-split any paragraph exceeding max_chars)
    normalized_paragraphs = []
    for p in paragraphs:
        if len(p) > max_chars:
            sentences = re.split(r"(?<=[.!?])\s+", p)
            current_s = ""
            for s in sentences:
                if len(current_s) + len(s) + 1 <= max_chars:
                    current_s = f"{current_s} {s}".strip() if current_s else s
                else:
                    if current_s:
                        normalized_paragraphs.append(current_s)
                    while len(s) > max_chars:
                        normalized_paragraphs.append(s[:max_chars])
                        s = s[max_chars:]
                    current_s = s
            if current_s:
                normalized_paragraphs.append(current_s)
        else:
            normalized_paragraphs.append(p)

    # Step 2: Assemble chunks from normalized paragraphs with overlap
    raw_chunks = []
    current_chunk = ""

    for p in normalized_paragraphs:
        if not current_chunk:
            current_chunk = p
        elif len(current_chunk) + len(p) + 2 <= max_chars:
            current_chunk = f"{current_chunk}\n\n{p}"
        else:
            raw_chunks.append(current_chunk)
            if overlap_chars > 0 and len(current_chunk) > overlap_chars:
                overlap = current_chunk[-overlap_chars:]
                candidate = f"{overlap}\n\n{p}"
                if len(candidate) <= max_chars:
                    current_chunk = candidate
                else:
                    current_chunk = p
            else:
                current_chunk = p

    if current_chunk:
        raw_chunks.append(current_chunk)

    # Step 3: Post-process merge tiny fragments without exceeding max_chars
    final_chunks = []
    for chunk in raw_chunks:
        chunk_str = chunk.strip()
        if not chunk_str:
            continue
        if final_chunks and len(chunk_str) < MIN_CHUNK_CHARS and (len(final_chunks[-1]) + len(chunk_str) + 2 <= max_chars):
            final_chunks[-1] += f"\n\n{chunk_str}"
        else:
            final_chunks.append(chunk_str)

    results = []
    for idx, content in enumerate(final_chunks):
        approx_tokens = max(1, len(content) // 4)
        results.append({
            "chunk_index": idx,
            "content": content,
            "token_count": approx_tokens,
        })

    return results

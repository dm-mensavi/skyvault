import logging
from pgvector.django import CosineDistance
from ai_features.models import DocumentChunk
from ai_features.services.embeddings import embed_text

logger = logging.getLogger(__name__)


def search_chunks(user, query: str, top_k: int = 5) -> list:
    """
    Performs pgvector cosine distance similarity search across DocumentChunks.
    Strictly scoped per user: all queries filter by file__user=user and file__trashed=False.
    """
    if not query or not query.strip():
        return []

    query_vector = embed_text(query)
    if not query_vector:
        logger.warning("Could not generate query embedding vector for search.")
        return []

    try:
        chunks = (
            DocumentChunk.objects.filter(file__user=user, file__trashed=False)
            .select_related("file", "analysis")
            .annotate(distance=CosineDistance("embedding", query_vector))
            .order_by("distance")[:top_k]
        )

        results = []
        for chunk in chunks:
            # CosineDistance ranges 0.0 (identical) to 2.0. Convert to similarity score [0..1]
            similarity = max(0.0, round(1.0 - (chunk.distance / 2.0), 3))
            chunk.relevance_score = similarity
            results.append(chunk)

        return results
    except Exception as e:
        logger.error(f"Error performing pgvector search_chunks: {e}", exc_info=True)
        return []


def search_files(user, query: str, top_k: int = 10) -> list:
    """
    Deduplicates chunk similarity results to return file-level search matches.
    Returns list of dicts: [{"file": File, "score": float, "snippet": str}]
    """
    matching_chunks = search_chunks(user, query, top_k=top_k * 2)
    if not matching_chunks:
        return []

    seen_files = set()
    file_results = []

    for chunk in matching_chunks:
        if chunk.file_id not in seen_files:
            seen_files.add(chunk.file_id)
            file_results.append({
                "file": chunk.file,
                "score": chunk.relevance_score,
                "snippet": chunk.content[:250] + "..." if len(chunk.content) > 250 else chunk.content,
                "tags": getattr(chunk.analysis, "tags", []),
            })
            if len(file_results) >= top_k:
                break

    return file_results

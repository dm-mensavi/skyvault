import logging
from pgvector.django import CosineDistance
from ai_features.models import DocumentChunk
from ai_features.services.embeddings import embed_text

logger = logging.getLogger(__name__)


class RetrievalUnavailable(Exception):
    """
    Raised when semantic search could not run at all — the embedding model failed
    to load, or the pgvector query itself errored (e.g. a dimension mismatch
    between the model and the DocumentChunk column).

    Distinct from an empty result list, which means retrieval worked and simply
    found nothing. Callers should surface these differently: "search is broken"
    is actionable, "no matching documents" is not.
    """


def search_chunks(user, query: str, top_k: int = 5) -> list:
    """
    Performs pgvector cosine distance similarity search across DocumentChunks.
    Strictly scoped per user: all queries filter by file__user=user and file__trashed=False.

    Returns [] when nothing matches. Raises RetrievalUnavailable when the search
    could not be performed at all.
    """
    if not query or not query.strip():
        return []

    query_vector = embed_text(query)
    if not query_vector:
        logger.warning("Could not generate query embedding vector for search.")
        raise RetrievalUnavailable(
            "The embedding model is unavailable, so semantic search could not run."
        )

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
        raise RetrievalUnavailable(f"The vector search query failed: {e}") from e


def search_files(user, query: str, top_k: int = 10) -> list:
    """
    Deduplicates chunk similarity results to return file-level search matches.
    Returns list of dicts: [{"file": File, "score": float, "snippet": str}]

    Propagates RetrievalUnavailable — see search_chunks.
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

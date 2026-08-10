import logging
from django.conf import settings

logger = logging.getLogger(__name__)

# Cached model singleton — loaded once per process, shared across all calls.
_model = None


def _get_model():
    """
    Lazily loads the sentence-transformers model.
    Uses 'all-MiniLM-L6-v2' (384 dims) — fast, free, no API key required.
    Model is cached in-process after first load.
    """
    global _model
    if _model is not None:
        return _model
    try:
        from sentence_transformers import SentenceTransformer
        model_name = getattr(settings, "AI_EMBEDDING_MODEL", "all-MiniLM-L6-v2")
        logger.info(f"Loading sentence-transformers model: {model_name}")
        _model = SentenceTransformer(model_name)
        logger.info("Embedding model loaded and cached.")
        return _model
    except ImportError:
        logger.error("sentence-transformers is not installed. Run: pip install sentence-transformers")
        return None
    except Exception as e:
        logger.error(f"Failed to load embedding model: {e}")
        return None


def embed_text(text: str) -> list[float]:
    """
    Generates a local embedding vector for a single text input.
    Model: all-MiniLM-L6-v2 (384 dimensions, runs in-process, no API key needed).
    Returns [] if model unavailable or text is empty.
    """
    if not text or not text.strip():
        return []

    model = _get_model()
    if model is None:
        logger.warning("Embedding model unavailable — returning empty vector.")
        return []

    try:
        vector = model.encode(text, normalize_embeddings=True)
        return vector.tolist()
    except Exception as e:
        logger.error(f"embed_text failed: {e}")
        return []


def embed_texts(texts: list[str]) -> list[list[float]]:
    """
    Generates batch embedding vectors for multiple text inputs.
    Runs all embeddings in a single batched forward pass — efficient.
    Returns [] if model unavailable or all inputs are empty.
    """
    cleaned = [t for t in texts if t and t.strip()]
    if not cleaned:
        return []

    model = _get_model()
    if model is None:
        logger.warning("Embedding model unavailable — returning empty batch.")
        return []

    try:
        vectors = model.encode(cleaned, normalize_embeddings=True, batch_size=32)
        return [v.tolist() for v in vectors]
    except Exception as e:
        logger.error(f"embed_texts batch failed: {e}")
        return []

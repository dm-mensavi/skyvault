import logging
from django.conf import settings

logger = logging.getLogger(__name__)


def get_openai_client():
    """
    Returns an instance of OpenAI client if API key is configured.
    Supports custom base_url endpoints (e.g. AgentRouter/OneAPI proxies).
    """
    api_key = getattr(settings, "OPENAI_API_KEY", "")
    if not api_key:
        return None
    base_url = getattr(settings, "OPENAI_BASE_URL", "")
    try:
        import openai
        kwargs = {"api_key": api_key}
        if base_url:
            kwargs["base_url"] = base_url
        return openai.OpenAI(**kwargs)
    except Exception as e:
        logger.error(f"Failed to initialize OpenAI client: {e}")
        return None


def embed_text(text: str) -> list[float]:
    """
    Generates embedding vector for a single text input using OpenAI API.
    Default model: text-embedding-3-small (1536 dimensions).
    """
    if not text or not text.strip():
        return []

    client = get_openai_client()
    if not client:
        logger.warning("OpenAI API key missing or client unavailable.")
        return []

    model = getattr(settings, "AI_EMBEDDING_MODEL", "text-embedding-3-small")
    dimensions = getattr(settings, "AI_EMBEDDING_DIMENSIONS", 1536)

    try:
        response = client.embeddings.create(
            input=text,
            model=model,
            dimensions=dimensions
        )
        return response.data[0].embedding
    except Exception as e:
        logger.error(f"OpenAI embedding generation failed: {e}")
        return []


def embed_texts(texts: list[str]) -> list[list[float]]:
    """
    Generates batch embedding vectors for multiple text inputs.
    """
    cleaned = [t for t in texts if t and t.strip()]
    if not cleaned:
        return []

    client = get_openai_client()
    if not client:
        logger.warning("OpenAI API key missing or client unavailable for batch embedding.")
        return []

    model = getattr(settings, "AI_EMBEDDING_MODEL", "text-embedding-3-small")
    dimensions = getattr(settings, "AI_EMBEDDING_DIMENSIONS", 1536)

    try:
        response = client.embeddings.create(
            input=cleaned,
            model=model,
            dimensions=dimensions
        )
        return [item.embedding for item in response.data]
    except Exception as e:
        logger.error(f"OpenAI batch embedding generation failed: {e}")
        return []

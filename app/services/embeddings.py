"""Vector embedding service using OpenAI."""
from typing import List
from app.core.config import settings
from openai import AsyncOpenAI

_client = None


def _get_client() -> AsyncOpenAI:
    """Get or create a singleton AsyncOpenAI client.

    The client is cached globally to avoid recreating it on each call.

    Returns:
        AsyncOpenAI: Initialized client instance.

    Raises:
        RuntimeError: If OPENAI_API_KEY is not configured in environment.
    """
    global _client
    if _client is None:
        if not settings.OPENAI_API_KEY:
            raise RuntimeError("OPENAI_API_KEY is required when EMBEDDINGS_PROVIDER=openai")
        _client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
    return _client


async def embed_texts(texts: List[str]) -> List[List[float]]:
    """Generate vector embeddings for text strings.

    Uses OpenAI's text-embedding-3-small model by default (1536 dimensions).
    All input texts are processed in a single batch request.

    Args:
        texts: List of strings to embed. Accepts empty list but individual
               empty strings may produce suboptimal embeddings.

    Returns:
        List[List[float]]: Embedding vectors in the same order as input texts.
                          Each vector is a list of floating-point numbers
                          representing semantic similarity space.

    Raises:
        RuntimeError: If OPENAI_API_KEY is not set.
        Exception: On API failures (connection issues, rate limiting,
                  authentication errors, etc.).

    Example:
        >>> texts = ["hello world", "goodbye world"]
        >>> embeddings = await embed_texts(texts)
        >>> len(embeddings)  # 2
        >>> len(embeddings[0])  # 1536
    """
    client = _get_client()
    resp = await client.embeddings.create(
        model=settings.OPENAI_EMBED_MODEL,
        input=texts,
    )
    # Response data is already sorted in the same order as input
    return [item.embedding for item in resp.data]

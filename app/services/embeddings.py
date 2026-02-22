from typing import List
from app.core.config import settings
from openai import AsyncOpenAI

_client = None

def _get_client() -> AsyncOpenAI:
    global _client
    if _client is None:
        if not settings.OPENAI_API_KEY:
            raise RuntimeError("OPENAI_API_KEY is required when EMBEDDINGS_PROVIDER=openai")
        _client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
    return _client

async def embed_texts(texts: List[str]) -> List[List[float]]:
    """
    OpenAI embeddings (no torch).
    Model: text-embedding-3-small (1536 dims).
    """
    client = _get_client()
    resp = await client.embeddings.create(
        model=settings.OPENAI_EMBED_MODEL,
        input=texts,
    )
    # resp.data is list in same order
    return [item.embedding for item in resp.data]
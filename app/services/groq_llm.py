"""LLM service using Groq API for fast inference."""
import httpx
from app.core.config import settings

GROQ_CHAT_URL = "https://api.groq.com/openai/v1/chat/completions"


async def groq_chat(messages: list[dict], temperature: float = 0.4) -> str:
    """Call Groq LLM API with a list of messages.

    Uses the Groq API which is compatible with OpenAI's chat completions
    interface. Designed for fast, cost-effective LLM inference on structured
    tasks like prompt generation and JSON output.

    Args:
        messages: List of message dictionaries, each with 'role' (system/user/assistant)
                 and 'content' (string). Example:
                 [
                     {"role": "system", "content": "You are a helpful..."},
                     {"role": "user", "content": "Generate..."}
                 ]
        temperature: Sampling temperature in range [0.0, 1.0]. Lower values
                    produce more deterministic/focused responses; higher values
                    introduce more randomness. Default 0.4 is good for
                    structured output. (default: 0.4)

    Returns:
        str: The text content of the model's response message.

    Raises:
        RuntimeError: If GROQ_API_KEY is not configured.
        httpx.HTTPError: On network or HTTP errors (status != 200).
        KeyError: If response structure is unexpected.
        Exception: On any other API-related failures.

    Example:
        >>> messages = [
        ...     {"role": "system", "content": "You are JSON generator."},
        ...     {"role": "user", "content": "Generate brand description."}
        ... ]
        >>> result = await groq_chat(messages, temperature=0.3)
        >>> # result is a JSON string
    """
    if not settings.GROQ_API_KEY:
        raise RuntimeError("GROQ_API_KEY environment variable is not set")

    headers = {"Authorization": f"Bearer {settings.GROQ_API_KEY}"}
    payload = {
        "model": settings.GROQ_MODEL,
        "messages": messages,
        "temperature": temperature,
    }

    async with httpx.AsyncClient(timeout=60) as client:
        r = await client.post(GROQ_CHAT_URL, headers=headers, json=payload)
        r.raise_for_status()  # Raise exception for non-2xx status codes
        data = r.json()
        return data["choices"][0]["message"]["content"]

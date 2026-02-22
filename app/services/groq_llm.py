import httpx
from app.core.config import settings

GROQ_CHAT_URL = "https://api.groq.com/openai/v1/chat/completions"

async def groq_chat(messages, temperature: float = 0.4) -> str:
    headers = {"Authorization": f"Bearer {settings.GROQ_API_KEY}"}
    payload = {
        "model": settings.GROQ_MODEL,
        "messages": messages,
        "temperature": temperature,
    }
    async with httpx.AsyncClient(timeout=60) as client:
        r = await client.post(GROQ_CHAT_URL, headers=headers, json=payload)
        r.raise_for_status()
        data = r.json()
        return data["choices"][0]["message"]["content"]
from google import genai
from google.genai import types
from app.core.config import settings

client = genai.Client(api_key=settings.GEMINI_API_KEY, http_options=types.HttpOptions(api_version="v1"))
models = client.models.list()
print([m.name for m in models][:30])
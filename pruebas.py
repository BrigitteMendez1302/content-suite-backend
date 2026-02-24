import os
from google import genai
from google.genai import types

API_KEY = os.environ.get("GEMINI_API_KEY")
if not API_KEY:
    raise SystemExit("Set GEMINI_API_KEY env var first")

# Para Developer API (AI Studio), muchas cuentas funcionan mejor con v1alpha.
client = genai.Client(
    api_key=API_KEY,
    http_options=types.HttpOptions(api_version="v1alpha"),
)

models = client.models.list()

print("AVAILABLE MODELS:")
for m in models:
    # m.name suele venir como "models/xxxx"
    name = getattr(m, "name", "")
    # Algunos modelos listan supported_actions o supported_methods (depende SDK)
    actions = getattr(m, "supported_actions", None) or getattr(m, "supported_methods", None)
    print("-", name, "| actions:", actions)
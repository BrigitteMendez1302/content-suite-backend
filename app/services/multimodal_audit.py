import json
import re
import time
from typing import Any, Dict
from google import genai
from app.core.config import settings
from google.genai import types


AUDIT_SYSTEM = (
    "Eres un auditor de cumplimiento de marca. "
    "Evalúa si la imagen cumple el manual de marca proporcionado. "
    "Devuelve SOLO JSON válido con claves: verdict, violations, notes. "
    "verdict: CHECK o FAIL. violations: lista de {rule,evidence,fix}."
)

def _extract_json(text: str) -> Dict[str, Any]:
    text = (text or "").strip()
    try:
        return json.loads(text)
    except Exception:
        m = re.search(r"\{.*\}", text, flags=re.DOTALL)
        if not m:
            raise ValueError("No JSON found in model output")
        return json.loads(m.group(0))

def audit_image_with_gemini(image_bytes: bytes, mime_type: str, brand_rules_text: str) -> Dict[str, Any]:
    if not settings.GEMINI_API_KEY:
        raise RuntimeError("GEMINI_API_KEY missing")

    client = genai.Client(
        api_key=settings.GEMINI_API_KEY,
        http_options=types.HttpOptions(api_version="v1"),
    )

    prompt = f"""Eres un auditor de cumplimiento de marca.
    Devuelve SOLO JSON válido con: verdict (CHECK|FAIL), violations[{{"rule","evidence","fix"}}], notes[].

    Reglas del manual (RAG):
    {brand_rules_text}
    """

    t0 = time.time()
    resp = client.models.generate_content(
        model=settings.GEMINI_MODEL,   # por ejemplo "gemini-1.5-flash"
        contents=[{
            "role": "user",
            "parts": [
                {"inline_data": {"mime_type": mime_type, "data": image_bytes}},
                {"text": prompt},
            ],
        }],
    )
    latency_ms = int((time.time() - t0) * 1000)

    out_text = getattr(resp, "text", None) or ""
    data = _extract_json(out_text)
    data["_latency_ms"] = latency_ms
    data["_raw"] = out_text[:4000]
    return data
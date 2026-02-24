import json
import time
from typing import Any, Dict, List
import google.generativeai as genai
from app.core.config import settings

AUDIT_SYSTEM = (
    "Eres un auditor de cumplimiento de marca. "
    "Debes evaluar si la imagen cumple el manual de marca proporcionado. "
    "Devuelve SOLO JSON válido con claves: verdict, violations, notes. "
    "verdict: CHECK o FAIL. "
    "violations: lista de {rule,evidence,fix}. "
    "Si no hay reglas visuales suficientes, usa FAIL con fix pidiendo especificación."
)

def _extract_json(text: str) -> Dict[str, Any]:
    # Best-effort extractor (Gemini puede envolver con texto)
    text = text.strip()
    try:
        return json.loads(text)
    except Exception:
        # find first {...}
        import re
        m = re.search(r"\{.*\}", text, flags=re.DOTALL)
        if not m:
            raise ValueError("No JSON found in model output")
        return json.loads(m.group(0))

def audit_image_with_gemini(image_bytes: bytes, mime_type: str, brand_rules_text: str) -> Dict[str, Any]:
    if not settings.GEMINI_API_KEY:
        raise RuntimeError("GEMINI_API_KEY missing")

    genai.configure(api_key=settings.GEMINI_API_KEY)
    model = genai.GenerativeModel(settings.GEMINI_MODEL)

    prompt = f"""{AUDIT_SYSTEM}

Reglas del manual (extraídas por RAG):
{brand_rules_text}

Instrucciones:
- Si cumple: verdict=CHECK y notes con 1-3 bullets.
- Si falla: verdict=FAIL y violations con reglas incumplidas y cómo corregir (acciones concretas).
"""

    t0 = time.time()
    resp = model.generate_content(
        [
            {"mime_type": mime_type, "data": image_bytes},
            prompt,
        ]
    )
    latency_ms = int((time.time() - t0) * 1000)

    out_text = resp.text or ""
    data = _extract_json(out_text)
    data["_latency_ms"] = latency_ms
    data["_raw"] = out_text[:4000]  # cap
    return data
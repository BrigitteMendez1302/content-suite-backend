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

    rule_gate = """
    Regla de veredicto (OBLIGATORIA):
    - Devuelve CHECK solo si puedes validar al menos 2 reglas VISUALES explícitas del manual
    (visual.colors, visual.logo_rules, visual.typography, visual.image_style).
    - Si el manual no contiene reglas visuales explícitas suficientes, devuelve FAIL con una violación:
    {"rule": "Faltan reglas visuales medibles", "evidence": "El manual no define colores/logo/tipografía/estilo de imagen medibles", "fix": "Agregar reglas visuales explícitas (colores permitidos, tamaño mínimo de logo, tipografía, estilo de imagen)"}.
    - Si una regla NO es auditable solo con imagen (ej: forbidden_terms, length_guidelines), NO la marques como violación:
    inclúyela en notes como 'no auditable con imagen sin texto'.

    Consistencia:
    - Si violations tiene al menos 1 ítem, verdict DEBE ser FAIL.
    - Solo verdict CHECK si violations está vacío.

    """

    prompt = f"""Eres un auditor de cumplimiento de marca.
    Devuelve SOLO JSON válido con: verdict (CHECK|FAIL), violations[{{"rule","evidence","fix"}}], notes[].

    {rule_gate}

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
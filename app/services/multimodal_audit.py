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
    "Devuelve SOLO JSON válido con claves: "
    "verdict, validated_rules_count, validated_rules, violations, notes. "
    "verdict: CHECK o FAIL. "
    "validated_rules_count: entero. "
    "validated_rules: lista corta (1-5) de reglas visuales que SÍ pudiste validar. "
    "violations: lista de {rule,evidence,fix}. "
    "notes: lista de strings."
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
    Reglas de veredicto (OBLIGATORIAS):

    1) CHECK mínimo:
    - Solo puedes proponer CHECK si validas AL MENOS 2 reglas visuales explícitas.
    - Debes reportar validated_rules_count y validated_rules (máx 5).

    2) Logo condicional:
    - Clasifica la imagen como "pieza_publicitaria" (post/banner/anuncio con layout/CTA/texto) o "foto_producto" (asset/foto sin layout).
    - Si es pieza_publicitaria: el logo ES obligatorio y se evalúa contra logo_rules.
    - Si es foto_producto: NO marques ausencia de logo como violación. En su lugar agrega una nota indicando que el logo no aplica/no se evalúa.

    3) Consistencia:
    - Si violations tiene al menos 1 ítem, verdict DEBE ser FAIL.
    - Solo puedes proponer CHECK si violations está vacío.

    4) No-auditable:
    - No conviertas en violaciones reglas no evaluables solo con imagen (texto, claims, reading level, etc.). Menciónalas en notes.
    """

    prompt = f"""
    {AUDIT_SYSTEM}

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
"""Multimodal image auditing using Google Gemini vision model."""
import json
import re
import time
from typing import Any, Dict
from google import genai
from app.core.config import settings
from google.genai import types


AUDIT_SYSTEM = (
    "Eres un auditor de cumplimiento de marca. "
    "Evalua si la imagen cumple el manual de marca proporcionado. "
    "Devuelve SOLO JSON valido con claves: "
    "verdict, validated_rules_count, validated_rules, violations, notes. "
    "verdict: CHECK o FAIL. "
    "validated_rules_count: entero. "
    "validated_rules: lista corta (1-5) de reglas visuales que SI pudiste validar. "
    "violations: lista de {rule,evidence,fix}. "
    "notes: lista de strings."
)


def _extract_json(text: str) -> Dict[str, Any]:
    """Extract JSON object from text, handling markdown code fences.

    Attempts direct JSON parsing first, then tries extracting the first
    {...} block if direct parsing fails. Useful for LLM outputs that may
    include markdown formatting.

    Args:
        text: String potentially containing JSON.

    Returns:
        dict: Parsed JSON object.

    Raises:
        ValueError: If no valid JSON found in text.
        json.JSONDecodeError: If extracted JSON is malformed.
    """
    text = (text or "").strip()
    try:
        return json.loads(text)
    except Exception:
        m = re.search(r"\{.*\}", text, flags=re.DOTALL)
        if not m:
            raise ValueError("No JSON found in model output")
        return json.loads(m.group(0))


def audit_image_with_gemini(
    image_bytes: bytes, mime_type: str, brand_rules_text: str
) -> Dict[str, Any]:
    """Audit an image against brand rules using Google Gemini vision model.

    Analyzes the provided image to check compliance with brand visual guidelines.
    Uses Gemini's multimodal capabilities to understand both visual content and
    text-based rules, returning a structured audit report.

    Args:
        image_bytes: Raw image file bytes.
        mime_type: MIME type of the image (e.g., "image/jpeg", "image/png").
        brand_rules_text: Pre-formatted text of relevant brand manual rules
                         from RAG. Should include sections like visual guidelines,
                         colors, typography, logo rules, etc.

    Returns:
        Dict[str, Any]: Audit report containing:
            - 'verdict': "CHECK" (pass), "FAIL" (violations found), or "REVIEW"
            - 'validated_rules_count': Number of rules successfully validated
            - 'validated_rules': List of rules confirmed in image (max 5)
            - 'violations': List of {rule, evidence, fix} objects
            - 'notes': List of additional observations
            - '_latency_ms': API call latency in milliseconds
            - '_raw': First 4000 chars of raw model output

    Raises:
        RuntimeError: If GEMINI_API_KEY is not configured in environment.
        Exception: On API failures, network errors, or JSON extraction failure.

    Rules for Verdict (enforced):
        - CHECK: At least 2 rules are explicitly validated against image
        - FAIL: If any violations are present, verdict must be FAIL
        - Logo: Only required for "pieza_publicitaria" (ads/posts with layout),
                NOT for "foto_producto" (product photos)

    Example:
        >>> result = audit_image_with_gemini(
        ...     image_bytes=img_data,
        ...     mime_type="image/jpeg",
        ...     brand_rules_text="Colors: [blue, white]\\nLogo: required..."
        ... )
        >>> print(result['verdict'])  # "CHECK" or "FAIL"
        >>> print(result['violations'])  # [{rule, evidence, fix}]
    """
    if not settings.GEMINI_API_KEY:
        raise RuntimeError("GEMINI_API_KEY missing")

    client = genai.Client(
        api_key=settings.GEMINI_API_KEY,
        http_options=types.HttpOptions(api_version="v1"),
    )

    rule_gate = """
    Reglas de veredicto (OBLIGATORIAS):

    1) CHECK minimo:
    - Solo puedes proponer CHECK si validas AL MENOS 2 reglas visuales explicitas.
    - Debes reportar validated_rules_count y validated_rules (max 5).

    2) Logo condicional:
    - Clasifica la imagen como "pieza_publicitaria" (post/banner/anuncio con layout/CTA/texto) o "foto_producto" (asset/foto sin layout).
    - Si es pieza_publicitaria: el logo ES obligatorio y se evalua contra logo_rules.
    - Si es foto_producto: NO marques ausencia de logo como violacion. En su lugar agrega una nota indicando que el logo no aplica/no se evalua.

    3) Consistencia:
    - Si violations tiene al menos 1 item, verdict DEBE ser FAIL.
    - Solo puedes proponer CHECK si violations esta vacio.

    4) No-auditable:
    - No conviertas en violaciones reglas no evaluables solo con imagen (texto, claims, reading level, etc.). Mencionalas en notes.
    """

    prompt = f"""
    {AUDIT_SYSTEM}

    {rule_gate}

    Reglas del manual (RAG):
    {brand_rules_text}
    """

    t0 = time.time()
    resp = client.models.generate_content(
        model=settings.GEMINI_MODEL,
        contents=[
            {
                "role": "user",
                "parts": [
                    {"inline_data": {"mime_type": mime_type, "data": image_bytes}},
                    {"text": prompt},
                ],
            }
        ],
    )
    latency_ms = int((time.time() - t0) * 1000)

    out_text = getattr(resp, "text", None) or ""
    data = _extract_json(out_text)
    data["_latency_ms"] = latency_ms
    data["_raw"] = out_text[:4000]
    return data

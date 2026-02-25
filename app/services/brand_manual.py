from typing import Dict, Any
from app.services.groq_llm import groq_chat

MANUAL_SYSTEM = (
    "Eres un Brand DNA Architect. "
    "Devuelve SOLO JSON válido, sin markdown, sin explicaciones. "
    "Respeta TIPOS estrictamente:\n"
    "- tone.dos/donts: arrays de strings\n"
    "- messaging.*: arrays de strings\n"
    "- style_rules.reading_level: SOLO 'simple' o 'medium'\n"
    "- style_rules.length_guidelines: objeto/dict\n"
    "- visual_guidelines.*: arrays de strings\n"
    "- approval_checklist: array de strings (mínimo 8 ítems)\n"
    "Si no tienes información, devuelve listas vacías o {} (NO strings)."
)

def build_manual_prompt(params: Dict[str, Any]) -> str:
    product = params["product"]
    tone = params["tone"]
    audience = params["audience"]
    brand_name = params.get("brand_name", product)
    extra = params.get("extra_constraints", "").strip()
    vr = params.get("visual_rules") or {}
    vr_colors = vr.get("colors") or []
    vr_logo = vr.get("logo_rules") or []
    vr_typo = vr.get("typography") or []
    vr_style = vr.get("image_style") or []
    vr_notes = vr.get("notes") or ""

    visual_block = f"""
    Visual Rules (FUENTE DE VERDAD DEL USUARIO):
    - colors: {vr_colors}
    - logo_rules: {vr_logo}
    - typography: {vr_typo}
    - image_style: {vr_style}
    - notes: {vr_notes}

    Regla NO NEGOCIABLE:
    - NO inventes reglas visuales nuevas.
    - Si alguna lista viene vacía, debe permanecer vacía en visual_guidelines y en notes indicar 'MISSING: user must define ...'.
    """

    schema_hint = """
Devuelve un JSON con estas claves:
brand_name, product, audience,
tone{description,dos[],donts[]},
messaging{value_props[],taglines[],forbidden_claims[],preferred_terms[],forbidden_terms[]},
style_rules{reading_level,length_guidelines},
visual_guidelines{colors[],logo_rules[],typography[],image_style[],notes},
examples{good[{type,text}],bad[{type,text,why}]},
approval_checklist[], assumptions[].
"""

    extra_block = f"\n- extra_constraints: {extra}\n" if extra else ""

    return f"""
Parámetros:
- brand_name: {brand_name}
- product: {product}
- tone: {tone}
- audience: {audience}{extra_block}

{visual_block}

{schema_hint}

Reglas:
- Sé específico en dos/donts y forbidden_terms.
- Si no tienes guías visuales, deja listas vacías y explica en visual_guidelines.notes.
- Incluye 2 ejemplos good y 2 bad (con "why").

Calidad mínima obligatoria:
- approval_checklist: mínimo 8 ítems verificables tipo checklist (NO puede ser vacío).
- style_rules.length_guidelines: usa defaults realistas si no se especifica canal:
  {{ "titulo": "<= 6 palabras", "descripcion": "<= 150 palabras", "guion_15s": "60-90 palabras" }}
- forbidden_claims: incluye 3-6 claims prohibidos específicos del producto. Si es bebida energética: NO prometer "cura fatiga", "rendimiento garantizado", "tratamiento", "efectos médicos".
""".strip()

async def generate_brand_manual(params: Dict[str, Any]) -> str:
    messages = [
        {"role": "system", "content": MANUAL_SYSTEM},
        {"role": "user", "content": build_manual_prompt(params)},
    ]
    return await groq_chat(messages)
from typing import Dict, Any, List
import time

from app.services.groq_llm import groq_chat
from app.repositories import brand_manual as manual_repo
from app.models.manual import BrandManual
from app.utils.json_repair import extract_json
from app.services.manual_normalize import normalize_manual_dict

MANUAL_SYSTEM = (
    "Eres un Brand DNA Architect. "
    "Devuelve SOLO JSON valido, sin markdown, sin explicaciones. "
    "Respeta TIPOS estrictamente:\n"
    "- tone.dos/donts: arrays de strings\n"
    "- messaging.*: arrays de strings\n"
    "- style_rules.reading_level: SOLO 'simple' o 'medium'\n"
    "- style_rules.length_guidelines: objeto/dict\n"
    "- visual_guidelines.*: arrays de strings\n"
    "- approval_checklist: array de strings (minimo 8 items)\n"
    "Si no tienes informacion, devuelve listas vacias o {} (NO strings)."
)


def build_manual_prompt(params: Dict[str, Any]) -> str:
    """Generate the textual prompt sent to the LLM.

    The prompt is long and includes instructions in Spanish along with the
    provided parameters. This helper only formats the input into the required
    block; no I/O or validation is performed here.
    """

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
    - Si alguna lista viene vacia, debe permanecer vacia en visual_guidelines y en notes indicar 'MISSING: user must define ...'.
    """

    schema_hint = """
Devuelve un JSON con estas claves:
brand_name, product, audience,
"""
    schema_hint += (
        "tone{description,dos[],donts[]},\n"
        "status: pending|approved,\n"
        "messaging{value_props[],taglines[],forbidden_claims[],preferred_terms[],forbidden_terms[]},\n"
        "style_rules{reading_level,length_guidelines},\n"
        "visual_guidelines{colors[],logo_rules[],typography[],image_style[],notes},\n"
        "examples{good[{type,text}],bad[{type,text,why}]},\n"
        "approval_checklist[], assumptions[].\n"
    )

    extra_block = f"\n- extra_constraints: {extra}\n" if extra else ""

    return f"""
Parametros:
- brand_name: {brand_name}
- product: {product}
- tone: {tone}
- audience: {audience}{extra_block}

{visual_block}

{schema_hint}

Reglas:
- Se especifico en dos/donts y forbidden_terms.
- Si no tienes guias visuales, deja listas vacias y explica en visual_guidelines.notes.

Calidad minima obligatoria:
- approval_checklist: minimo 8 items verificables tipo checklist (NO puede ser vacio).
- style_rules.length_guidelines: usa defaults realistas si no se especifica canal:
  {{ "titulo": "<= 6 palabras", "descripcion": "<= 150 palabras", "guion_15s": "60-90 palabras" }}
- forbidden_claims: incluye 3-6 claims prohibidos especificos del producto. Si es bebida energetica: NO prometer "cura fatiga", "rendimiento garantizado", "tratamiento", "efectos medicos".
""".strip()


async def generate_brand_manual(params: Dict[str, Any]) -> str:
    """Send the prompt to the LLM and return raw text output.

    The returned string may contain extraneous characters; callers should parse
    it before use. This call does not perform any network logic beyond calling
    ``groq_chat``.
    """

    messages = [
        {"role": "system", "content": MANUAL_SYSTEM},
        {"role": "user", "content": build_manual_prompt(params)},
    ]
    return await groq_chat(messages)


def _parse_and_validate(raw: str) -> Dict[str, Any]:
    """Convert a raw LLM string into a validated manual dictionary.

    - repairs malformed JSON using ``extract_json``
    - normalizes field types via ``normalize_manual_dict``
    - validates the result with the ``BrandManual`` Pydantic model

    Raises ``ValidationError`` or related exceptions on failure.
    """

    parsed = extract_json(raw)
    parsed = normalize_manual_dict(parsed)
    manual = BrandManual.model_validate(parsed).model_dump()
    return manual


async def create_brand_manual(brand_id: str, params: Dict[str, Any]) -> Dict[str, Any]:
    """High-level helper used by the route when a new manual is requested.

    1. fetch visual rules from the repo
    2. merge them into params
    3. generate raw text from the LLM
    4. parse + validate JSON
    5. insert manual row and obtain id
    6. chunk the manual, embed and store chunk rows

    Returns a dictionary containing the new manual id, the JSON itself, the
    number of chunks stored, and the elapsed latency in milliseconds.
    """

    t0 = time.time()

    # fetch visual rules from repository and merge into params
    visual_rules = manual_repo.get_visual_rules(brand_id)
    params = {**params, "visual_rules": visual_rules}

    # generate with LLM and validate
    raw = await generate_brand_manual(params)
    manual = _parse_and_validate(raw)

    # persist manual and obtain its id
    manual_id = manual_repo.insert_manual(brand_id, manual)
    if not manual_id:
        raise RuntimeError("database insert failed")

    # build chunks, embed and store
    from app.services.chunking import chunk_manual
    from app.services.embeddings import embed_texts

    chunks = chunk_manual(manual)
    texts = [c["chunk_text"] for c in chunks]
    vectors = await embed_texts(texts)

    payload: List[Dict[str, Any]] = []
    for c, v in zip(chunks, vectors):
        payload.append(
            {
                "brand_manual_id": manual_id,
                "section": c["section"],
                "chunk_text": c["chunk_text"],
                "embedding": v,
                "metadata": c["metadata"],
            }
        )

    if not manual_repo.insert_manual_chunks(manual_id, payload):
        raise RuntimeError("failed to store manual chunks")

    latency_ms = int((time.time() - t0) * 1000)
    return {
        "brand_id": brand_id,
        "manual_id": manual_id,
        "manual_json": manual,
        "chunks_indexed": len(payload),
        "latency_ms": latency_ms,
    }

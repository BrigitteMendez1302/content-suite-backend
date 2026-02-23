from typing import List, Dict

# pesos base por "tipo de sección" (más alto = más prioridad)
BASE_SECTION_WEIGHTS = [
    ("messaging.forbidden_claims", 100),
    ("messaging.forbidden_terms", 100),
    ("tone.donts", 90),
    ("tone.dos", 85),
    ("style_rules", 80),             # reading_level/length_guidelines
    ("approval_checklist", 75),
    ("messaging.preferred_terms", 70),
    ("messaging.value_props", 65),
    ("messaging.taglines", 60),
    ("visual.logo_rules", 40),
    ("visual.typography", 35),
    ("visual.colors", 35),
    ("visual.image_style", 30),
    ("visual.notes", 20),
    ("examples.bad", 15),
    ("examples.good", 10),
]

def _weight_for_section(section: str) -> int:
    section = (section or "").strip()
    for prefix, w in BASE_SECTION_WEIGHTS:
        if section == prefix or section.startswith(prefix):
            return w
    return 0

def rerank_chunks(chunks: List[Dict], content_type: str, keep_k: int = 6) -> List[Dict]:
    """
    Rerank = combine semantic similarity + rule-priority by section.
    Assumes similarity in [0..1] where higher is better.
    """
    def score(c: Dict) -> float:
        w = _weight_for_section(c.get("section", ""))
        sim = c.get("similarity") or 0.0

        # tipo de contenido: prioriza un poco distinto
        # - image_prompt: visual.* sube
        # - video_script: tone + forbidden* sube
        # - product_description: forbidden* + value_props + preferred_terms sube
        if content_type == "image_prompt":
            if (c.get("section") or "").startswith("visual."):
                w += 25
        elif content_type == "video_script":
            if (c.get("section") or "").startswith("tone."):
                w += 10
        elif content_type == "product_description":
            if (c.get("section") or "").startswith("messaging.value_props"):
                w += 10
            if (c.get("section") or "").startswith("messaging.preferred_terms"):
                w += 10

        # score final: peso domina, similarity desempata
        # (multiplico peso para que domine claramente)
        return (w * 1000.0) + (sim * 100.0)

    ranked = sorted(chunks, key=score, reverse=True)
    return ranked[:keep_k]
"""Re-ranking service for RAG chunk retrieval.

This module combines semantic similarity scores with rule-based section
weights to produce relevance scores for brand manual chunks.
"""
from typing import List, Dict

# Priority weights for different manual sections
# Higher values = higher retrieval priority
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
    """Lookup base priority weight for a section.

    Args:
        section: Section identifier (e.g., "tone.dos").

    Returns:
        int: Weight from BASE_SECTION_WEIGHTS if section matches a prefix,
             otherwise 0 (lowest priority).
    """
    section = (section or "").strip()
    for prefix, w in BASE_SECTION_WEIGHTS:
        if section == prefix or section.startswith(prefix):
            return w
    return 0


def rerank_chunks(
    chunks: List[Dict], content_type: str, keep_k: int = 6
) -> List[Dict]:
    """Re-rank and filter RAG chunks by combined semantic + rule-based score.

    Combines semantic similarity (from embeddings) with section-based priority
    weights, optionally boosted based on content type. This ensures that
    critical brand rules (forbidden claims, tone dos/donts) appear first in
    the RAG context, even if semantic similarity is moderate.

    Args:
        chunks: List of chunk dicts from the vector store, each with keys:
               - 'section': Section identifier (e.g., "tone.dos")
               - 'similarity': Float in [0, 1] from semantic search
               - Other keys are preserved
        content_type: Type of content being generated. Affects weighting:
                     - "image_prompt": boosts visual.* sections
                     - "video_script": boosts tone.* and forbidden* sections
                     - "product_description": boosts messaging sections
        keep_k: Number of top chunks to return. (default: 6)

    Returns:
        List[Dict]: Top k chunks re-ranked by combined score (highest first).
                   Original dicts are preserved with all fields intact.

    Scoring Algorithm:
        score = (base_weight * 1000.0) + (similarity * 100.0) + type_bonus
        - Base weight dominates (multiplier = 1000) to ensure rule priority
        - Similarity acts as a tiebreaker (multiplier = 100)
        - Type bonus is small (10-25) for content-specific refinement

    Example:
        >>> chunks = [
        ...     {"section": "tone.dos", "similarity": 0.8, ...},
        ...     {"section": "examples.good", "similarity": 0.95, ...}
        ... ]
        >>> reranked = rerank_chunks(chunks, "product_description", keep_k=2)
        >>> reranked[0]["section"]  # "tone.dos" ranked first by weight
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
from typing import Any, Dict, List, Tuple

def chunk_manual(manual: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Break down a brand manual into semantically meaningful chunks for embeddings.

    Each chunk represents a logical section of the manual (e.g., "tone.dos",
    "messaging.forbidden_claims") and is designed to be independently embedded
    and retrieved during RAG operations. Empty sections are skipped.

    Args:
        manual: A validated brand manual dictionary containing keys like:
               - tone: {description, dos[], donts[]}
               - messaging: {value_props[], taglines[], forbidden_claims[], ...}
               - style_rules: {reading_level, length_guidelines}
               - visual_guidelines: {colors[], logo_rules[], typography[], ...}
               - examples: {good[], bad[]}
               - approval_checklist: []
               - assumptions: []

    Returns:
        List[Dict[str, Any]]: List of chunk dictionaries, each with:
            - 'section': String identifier (e.g., "tone.dos")
            - 'chunk_text': The actual content to embed
            - 'metadata': Optional dict for tracking (empty for now)

    Note:
        - Empty strings or empty sections are skipped entirely.
        - Multi-item lists are joined with newlines for compact representation.
        - Examples are formatted as '{type}: {text}' with reasons included
          for bad examples.

    Example:
        >>> manual = {"tone": {"description": "...", "dos": [...], ...}, ...}
        >>> chunks = chunk_manual(manual)
        >>> len(chunks)
        >>> chunks[0]['section']
        'tone.description'
    """
    chunks: List[Dict[str, Any]] = []

    def add(section: str, text: str, metadata: Dict[str, Any] | None = None):
        if not text.strip():
            return
        chunks.append({
            "section": section,
            "chunk_text": text.strip(),
            "metadata": metadata or {}
        })

    add("tone.description", manual["tone"]["description"])
    add("tone.dos", "\n".join(manual["tone"].get("dos", [])))
    add("tone.donts", "\n".join(manual["tone"].get("donts", [])))

    m = manual.get("messaging", {})
    add("messaging.value_props", "\n".join(m.get("value_props", [])))
    add("messaging.taglines", "\n".join(m.get("taglines", [])))
    add("messaging.forbidden_claims", "\n".join(m.get("forbidden_claims", [])))
    add("messaging.preferred_terms", "\n".join(m.get("preferred_terms", [])))
    add("messaging.forbidden_terms", "\n".join(m.get("forbidden_terms", [])))

    sr = manual.get("style_rules", {})
    add("style_rules.reading_level", str(sr.get("reading_level", "")))
    lg = sr.get("length_guidelines", {})
    if lg:
        add("style_rules.length_guidelines", "\n".join([f"{k}: {v}" for k, v in lg.items()]))

    vg = manual.get("visual_guidelines", {})
    add("visual.colors", "\n".join(vg.get("colors", [])))
    add("visual.logo_rules", "\n".join(vg.get("logo_rules", [])))
    add("visual.typography", "\n".join(vg.get("typography", [])))
    add("visual.image_style", "\n".join(vg.get("image_style", [])))
    add("visual.notes", str(vg.get("notes") or ""))

    ex = manual.get("examples", {})
    good = ex.get("good", [])
    bad = ex.get("bad", [])
    if good:
        add("examples.good", "\n\n".join([f"{i.get('type')}: {i.get('text')}" for i in good]))
    if bad:
        add("examples.bad", "\n\n".join([f"{i.get('type')}: {i.get('text')} (why: {i.get('why','')})" for i in bad]))

    add("approval_checklist", "\n".join(manual.get("approval_checklist", [])))
    add("assumptions", "\n".join(manual.get("assumptions", [])))

    return chunks
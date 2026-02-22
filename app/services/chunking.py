from typing import Any, Dict, List, Tuple

def chunk_manual(manual: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Deterministic chunking: one chunk per meaningful section/list.
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
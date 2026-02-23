from typing import Any, Dict

def _ensure_list(v: Any) -> list:
    if v is None:
        return []
    if isinstance(v, list):
        return v
    if isinstance(v, str):
        # separa por saltos o puntos si te vino en un solo string
        parts = [p.strip(" -•\t") for p in v.replace("\r", "").split("\n")]
        parts = [p for p in parts if p]
        return parts if parts else [v.strip()]
    return [str(v)]

def _ensure_dict(v: Any) -> dict:
    if v is None:
        return {}
    if isinstance(v, dict):
        return v
    if isinstance(v, str):
        # fallback: lo dejamos como una key "notes"
        return {"notes": v}
    return {"value": v}

def normalize_manual_dict(m: Dict[str, Any]) -> Dict[str, Any]:
    # style_rules
    sr = m.get("style_rules") or {}
    rl = sr.get("reading_level", "simple")
    if isinstance(rl, str):
        low = rl.lower()
        if "med" in low:
            rl = "medium"
        else:
            # todo lo demás lo consideramos simple
            rl = "simple"
    sr["reading_level"] = rl
    sr["length_guidelines"] = _ensure_dict(sr.get("length_guidelines"))
    m["style_rules"] = sr

    # visual_guidelines
    vg = m.get("visual_guidelines") or {}
    vg["colors"] = _ensure_list(vg.get("colors"))
    vg["logo_rules"] = _ensure_list(vg.get("logo_rules"))
    vg["typography"] = _ensure_list(vg.get("typography"))
    vg["image_style"] = _ensure_list(vg.get("image_style"))
    m["visual_guidelines"] = vg

    # messaging lists
    msg = m.get("messaging") or {}
    for k in ["value_props", "taglines", "forbidden_claims", "preferred_terms", "forbidden_terms"]:
        msg[k] = _ensure_list(msg.get(k))
    m["messaging"] = msg

    # tone lists
    tone = m.get("tone") or {}
    tone["dos"] = _ensure_list(tone.get("dos"))
    tone["donts"] = _ensure_list(tone.get("donts"))
    m["tone"] = tone

    # approval_checklist / assumptions
    m["approval_checklist"] = _ensure_list(m.get("approval_checklist"))
    m["assumptions"] = _ensure_list(m.get("assumptions"))

    return m
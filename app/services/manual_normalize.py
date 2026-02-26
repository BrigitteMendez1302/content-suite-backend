"""Normalization utilities for brand manual data structures.

Handles conversion of LLM-generated manual data into consistent, validated
dictionary structures with proper types (lists, dicts) and fallback values.
"""
from typing import Any, Dict


def _ensure_list(v: Any) -> list:
    """Convert various value types to a list.

    Handles string-to-list conversion by splitting on newlines and cleaning,
    converts None to empty list, and wraps scalars as single-element lists.

    Args:
        v: Value of any type (None, list, string, scalar).

    Returns:
        list: Converted value as list. If input is None, returns [].
             If string, splits by newlines and strips bullets (-, •, \t).
             If already list, returns as-is. Otherwise wraps in list.

    Examples:
        >>> _ensure_list("• Item 1\\n- Item 2")
        ['Item 1', 'Item 2']

        >>> _ensure_list(None)
        []

        >>> _ensure_list(["a", "b"])
        ['a', 'b']

        >>> _ensure_list("single value")
        ['single value']
    """
    if v is None:
        return []
    if isinstance(v, list):
        return v
    if isinstance(v, str):
        parts = [p.strip(" -•\t") for p in v.replace("\r", "").split("\n")]
        parts = [p for p in parts if p]
        return parts if parts else [v.strip()]
    return [str(v)]


def _ensure_dict(v: Any) -> dict:
    """Convert various value types to a dictionary.

    Handles None as empty dict, preserves dict, converts string to
    {"notes": string}, and other types to {"value": value}.

    Args:
        v: Value of any type (None, dict, string, scalar).

    Returns:
        dict: Converted value as dict. If None, returns {}.
             If already dict, returns as-is. If string, returns
             {"notes": v}. Otherwise returns {"value": v}.

    Examples:
        >>> _ensure_dict("Some notes")
        {'notes': 'Some notes'}

        >>> _ensure_dict(None)
        {}

        >>> _ensure_dict({"key": "value"})
        {'key': 'value'}

        >>> _ensure_dict(123)
        {'value': 123}
    """
    if v is None:
        return {}
    if isinstance(v, dict):
        return v
    if isinstance(v, str):
        return {"notes": v}
    return {"value": v}


def normalize_manual_dict(m: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize brand manual structure with consistent types and structure.

    Ensures all nested fields follow expected schema:
    - Style rules reading_level normalized to "simple" or "medium"
    - Visual guidelines lists properly formatted
    - Messaging fields converted to lists
    - Tone dos/donts as lists
    - Checklists and assumptions as lists

    Args:
        m: Raw brand manual dict from LLM generation (may have inconsistent
           types and structure).

    Returns:
        dict: Normalized manual with all fields as proper types:
             * style_rules: dict with reading_level, length_guidelines
             * visual_guidelines: dict with lists for colors, logo_rules, etc.
             * messaging: dict with lists for value_props, taglines, etc.
             * tone: dict with dos, donts lists
             * approval_checklist: list
             * assumptions: list

    Note:
        - Reading level: "medium" for strings containing "med", otherwise "simple"
        - None values converted to empty containers
        - String values in list fields split by newlines
    """
    # style_rules
    sr = m.get("style_rules") or {}
    rl = sr.get("reading_level", "simple")
    if isinstance(rl, str):
        low = rl.lower()
        if "med" in low:
            rl = "medium"
        else:
            # Consider everything else as simple
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
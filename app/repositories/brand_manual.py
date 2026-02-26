from typing import Any, Dict, List, Optional

from app.db.supabase_client import get_supabase


# database operations related to brand manuals and visual rules

def get_visual_rules(brand_id: str) -> Dict[str, Any]:
    """Fetch the visual rules row for a brand.

    Returns a dict with keys colors, logo_rules, typography, image_style, notes
    or an empty structure if nothing is found. The caller can rely on the
    returned object having those fields (they may be empty lists or None).
    """
    sb = get_supabase()
    res = (
        sb.table("brand_visual_rules")
        .select("*")
        .eq("brand_id", brand_id)
        .limit(1)
        .execute()
    )
    if res.data:
        return res.data[0]
    return {"colors": [], "logo_rules": [], "typography": [], "image_style": [], "notes": None}


def upsert_visual_rules(brand_id: str, rules: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Insert or update visual rules for a brand.

    `rules` should contain the keys ``colors``, ``logo_rules``, ``typography``,
    ``image_style`` and ``notes``.  The returned object is the saved row from
    Supabase, or ``None`` if the operation failed.
    """
    sb = get_supabase()
    payload = {"brand_id": brand_id, **rules}
    res = sb.table("brand_visual_rules").upsert(payload).execute()
    if res.data:
        return res.data[0]
    return None


def insert_manual(brand_id: str, manual: Dict[str, Any]) -> Optional[str]:
    """Insert a validated manual JSON into the database.

    Returns the newly created manual id, or None if the insert failed.
    """
    sb = get_supabase()
    res = sb.table("brand_manuals").insert({"brand_id": brand_id, "manual_json": manual}).execute()
    if res.data:
        return res.data[0]["id"]
    return None


def get_latest_manual(brand_id: str) -> Optional[Dict[str, Any]]:
    """Return the latest manual record (including id) for a brand.

    The record has keys id, brand_id, manual_json, version, created_at.
    If no manual exists, returns None.
    """
    sb = get_supabase()
    res = (
        sb.table("brand_manuals")
        .select("id, brand_id, manual_json, version, created_at")
        .eq("brand_id", brand_id)
        .order("created_at", desc=True)
        .limit(1)
        .execute()
    )
    if res.data:
        return res.data[0]
    return None


def insert_manual_chunks(manual_id: str, payload: List[Dict[str, Any]]) -> bool:
    """Insert a list of chunks for a given manual id.

    Payload is assumed to contain dictionaries already in the correct shape
    (refer to routes/brands.py for expected keys). Returns True if the
    insertion succeeded, False otherwise.
    """
    sb = get_supabase()
    res = sb.table("brand_manual_chunks_openai").insert(payload).execute()
    return bool(res.data)

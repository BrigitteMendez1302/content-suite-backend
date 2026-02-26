from typing import Any, Dict, Optional

from app.db.supabase_client import get_supabase


def get_manual_by_id(manual_id: str) -> Optional[Dict[str, Any]]:
    """Return a manual row given its primary key, or None if not found."""
    sb = get_supabase()
    res = (
        sb.table("brand_manuals")
        .select("id, brand_id, manual_json, created_at")
        .eq("id", manual_id)
        .limit(1)
        .execute()
    )
    if res.data:
        return res.data[0]
    return None

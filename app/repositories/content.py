from typing import Any, Dict, List, Optional

from app.db.supabase_client import get_supabase


def insert_content_item(
    brand_id: str,
    manual_id: str,
    content_type: str,
    brief: str,
    output_text: str,
    rag_chunks: List[Dict[str, Any]],
    status: str = "PENDING",
) -> Optional[str]:
    """Insert a generated content item into the database.

    Returns the new row's id on success, or ``None`` if the insert failed.
    """
    sb = get_supabase()
    res = sb.table("content_items").insert(
        {
            "brand_id": brand_id,
            "brand_manual_id": manual_id,
            "type": content_type,
            "input_brief": brief,
            "output_text": output_text,
            "status": status,
            "rag_chunks": rag_chunks,
        }
    ).execute()
    if res.data and len(res.data) > 0:
        return res.data[0].get("id")
    return None


def get_content_item(content_id: str) -> Optional[Dict[str, Any]]:
    """Fetch a single content item by its id.

    Used for read endpoints or tests. Returns ``None`` if not found.
    """
    sb = get_supabase()
    res = (
        sb.table("content_items")
        .select("*")
        .eq("id", content_id)
        .limit(1)
        .execute()
    )
    if res.data:
        return res.data[0]
    return None

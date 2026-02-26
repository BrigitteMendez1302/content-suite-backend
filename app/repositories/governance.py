from typing import Any, Dict, List, Optional

from app.db.supabase_client import get_supabase


def fetch_content_for_inbox(profile: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Return a list of content items appropriate for the given user profile.

    Creators receive their own items; approvers receive all pending items.
    The returned list is limited to the most recent 50 rows.
    """
    sb = get_supabase()
    role = profile.get("role")
    if role == "creator":
        res = (
            sb.table("content_items")
            .select("id, brand_id, type, status, input_brief, output_text, created_at, brand_manual_id")
            .eq("created_by", profile.get("id"))
            .order("created_at", desc=True)
            .limit(50)
            .execute()
        )
        return res.data or []
    else:
        # approvers see pending items
        res = (
            sb.table("content_items")
            .select("id, brand_id, type, status, input_brief, output_text, created_at, brand_manual_id")
            .eq("status", "PENDING")
            .order("created_at", desc=True)
            .limit(50)
            .execute()
        )
        return res.data or []


def get_content_item(content_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve a single content item by id or None if not found."""
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


def update_content_status(content_id: str, status: str) -> bool:
    """Set the status of a content item. Returns True if row existed."""
    sb = get_supabase()
    upd = sb.table("content_items").update({"status": status}).eq("id", content_id).execute()
    return bool(upd.data)


def insert_approval(
    content_id: str,
    role: str,
    decision: str,
    comment: Optional[str],
    created_by: str,
) -> None:
    """Record an approval/rejection event in the approvals table."""
    sb = get_supabase()
    sb.table("approvals").insert(
        {
            "content_item_id": content_id,
            "role": role,
            "decision": decision,
            "comment": comment,
            "created_by": created_by,
        }
    ).execute()


def insert_audit_report(
    content_id: str,
    image_path: str,
    image_url: Optional[str],
    verdict: str,
    report_json: Dict[str, Any],
    created_by: str,
) -> None:
    """Persist an image audit report tied to a content item."""
    sb = get_supabase()
    sb.table("audit_images").insert(
        {
            "content_item_id": content_id,
            "image_path": image_path,
            "image_public_url": image_url,
            "verdict": verdict,
            "report_json": report_json,
            "created_by": created_by,
        }
    ).execute()

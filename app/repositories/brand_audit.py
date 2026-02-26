from typing import Any, Dict, List, Optional

from app.db.supabase_client import get_supabase


# repository functions for brand audit-related persistence and retrieval

def get_latest_manual_id(brand_id: str) -> Optional[str]:
    """Return the most recent manual id for a given brand, or None if there is none."""
    sb = get_supabase()
    mres = (
        sb.table("brand_manuals")
        .select("id, created_at")
        .eq("brand_id", brand_id)
        .order("created_at", desc=True)
        .limit(1)
        .execute()
    )
    if mres.data:
        return mres.data[0]["id"]
    return None


def insert_audit_report(
    brand_id: str,
    manual_id: str,
    image_path: str,
    image_url: Optional[str],
    verdict: str,
    report_json: Dict[str, Any],
    created_by: str,
) -> None:
    """Persist an audit image report in the database."""
    sb = get_supabase()
    sb.table("brand_audit_images").insert(
        {
            "brand_id": brand_id,
            "brand_manual_id": manual_id,
            "image_path": image_path,
            "image_public_url": image_url,
            "verdict": verdict,
            "report_json": report_json,
            "created_by": created_by,
        }
    ).execute()


def match_manual_chunks(
    manual_id: str, qvec: List[float], match_count: int = 12
) -> List[Dict[str, Any]]:
    """Call the Supabase RPC that performs vector matching on manual chunks.

    Returns a list of chunk dictionaries (could be empty).
    """
    sb = get_supabase()
    rpc = sb.rpc(
        "match_brand_manual_chunks_openai",
        {
            "p_brand_manual_id": manual_id,
            "p_query_embedding": qvec,
            "p_match_count": match_count,
        },
    ).execute()
    return rpc.data or []

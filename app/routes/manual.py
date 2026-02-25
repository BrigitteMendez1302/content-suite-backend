from fastapi import APIRouter, HTTPException
from app.db.supabase_client import get_supabase

router = APIRouter(prefix="/manuals", tags=["manuals"])

@router.get("/{manual_id}")
def get_manual(manual_id: str):
    sb = get_supabase()
    res = (
        sb.table("brand_manuals")
        .select("id, brand_id, manual_json, created_at")
        .eq("id", manual_id)
        .limit(1)
        .execute()
    )
    if not res.data:
        raise HTTPException(status_code=404, detail="Manual not found")
    return res.data[0]
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from app.db.supabase_client import get_supabase
from app.core.auth import require_roles

router = APIRouter(prefix="/brands", tags=["visual-rules"])

class VisualRulesBody(BaseModel):
    colors: list[str] = []
    logo_rules: list[str] = []
    typography: list[str] = []
    image_style: list[str] = []
    notes: str | None = None

@router.get("/{brand_id}/visual-rules")
async def get_visual_rules(brand_id: str, profile=Depends(require_roles("creator","approver_a","approver_b"))):
    sb = get_supabase()
    res = sb.table("brand_visual_rules").select("*").eq("brand_id", brand_id).limit(1).execute()
    if not res.data:
        return {"brand_id": brand_id, "colors": [], "logo_rules": [], "typography": [], "image_style": [], "notes": None}
    return res.data[0]

@router.put("/{brand_id}/visual-rules")
async def upsert_visual_rules(brand_id: str, body: VisualRulesBody, profile=Depends(require_roles("creator","approver_b"))):
    sb = get_supabase()
    payload = {
        "brand_id": brand_id,
        "colors": body.colors,
        "logo_rules": body.logo_rules,
        "typography": body.typography,
        "image_style": body.image_style,
        "notes": body.notes,
    }
    # upsert by PK
    res = sb.table("brand_visual_rules").upsert(payload).execute()
    if not res.data:
        raise HTTPException(status_code=500, detail="Failed to save visual rules")
    return res.data[0]
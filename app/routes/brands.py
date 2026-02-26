from fastapi import APIRouter, HTTPException

from app.db.supabase_client import get_supabase
from app.models.brand import BrandCreateRequest, BrandCreateResponse
from app.services.brand_manual import create_brand_manual
from app.repositories import brand_manual as manual_repo

router = APIRouter(prefix="/brands", tags=["brands"])

@router.post("", response_model=BrandCreateResponse)
def create_brand(req: BrandCreateRequest):
    sb = get_supabase()
    res = sb.table("brands").insert({"name": req.name}).execute()
    if not res.data:
        raise HTTPException(status_code=500, detail="Failed to create brand")
    row = res.data[0]
    return BrandCreateResponse(id=row["id"], name=row["name"])

@router.post("/{brand_id}/manual")
async def create_manual(brand_id: str, body: dict):
    """Endpoint that creates a new Brand DNA manual.

    The heavy lifting is delegated to ``services.brand_manual.create_brand_manual``
    which encapsulates prompt generation, LLM invocation, validation and
    persistence. This route remains responsible for raising HTTP errors if the
    service raises unexpected exceptions.
    """

    try:
        return await create_brand_manual(brand_id, body)
    except HTTPException:
        # propagate any HTTPExceptions raised by lower layers
        raise
    except Exception as exc:
        # unexpected failures are converted into 500s
        raise HTTPException(status_code=500, detail=str(exc))

@router.get("/{brand_id}/manual")
def get_latest_manual(brand_id: str):
    """Return the most recent manual for a brand (cached by repo)."""
    rec = manual_repo.get_latest_manual(brand_id)
    if not rec:
        raise HTTPException(status_code=404, detail="No manual found for brand")
    return rec

@router.get("")
def list_brands():
    sb = get_supabase()
    res = (
        sb.table("brands")
        .select("id, name, created_at")
        .order("created_at", desc=True)
        .limit(50)
        .execute()
    )
    return res.data or []

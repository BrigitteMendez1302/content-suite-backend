from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Optional

from app.core.auth import require_roles
from app.services.visual_rules import get_rules, upsert_rules

router = APIRouter(prefix="/brands", tags=["visual-rules"])


class VisualRulesBody(BaseModel):
    colors: list[str] = []
    logo_rules: list[str] = []
    typography: list[str] = []
    image_style: list[str] = []
    notes: Optional[str] = None


@router.get("/{brand_id}/visual-rules")
async def get_visual_rules(brand_id: str, profile=Depends(require_roles("creator","approver_a","approver_b"))):
    """Retrieve stored visual rules for a brand (or defaults)."""
    return get_rules(brand_id)


@router.put("/{brand_id}/visual-rules")
async def upsert_visual_rules(brand_id: str, body: VisualRulesBody):
    """Insert or update the visual rules for a brand."""
    payload = body.model_dump()
    return upsert_rules(brand_id, payload)

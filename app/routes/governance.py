from fastapi import APIRouter, Depends, UploadFile, File
from pydantic import BaseModel
from typing import Optional

from app.core.auth import get_current_profile, require_roles
from app.services.governance import inbox, approve, reject, audit_image as audit_image_service

router = APIRouter(tags=["governance"])


class DecisionBody(BaseModel):
    comment: Optional[str] = None


@router.get("/inbox")
async def inbox_endpoint(profile=Depends(get_current_profile)):
    """Return the user's governance inbox (creator or approver view)."""
    return {"items": inbox(profile)}


@router.post("/content/{content_id}/approve")
async def approve_endpoint(
    content_id: str, body: DecisionBody, profile=Depends(require_roles("approver_a", "approver_b"))
):
    """Approve a piece of content."""
    return approve(content_id, body.comment, profile)


@router.post("/content/{content_id}/reject")
async def reject_endpoint(
    content_id: str, body: DecisionBody, profile=Depends(require_roles("approver_a", "approver_b"))
):
    """Reject a piece of content."""
    return reject(content_id, body.comment, profile)


@router.post("/content/{content_id}/audit-image")
async def audit_image(
    content_id: str,
    file: UploadFile = File(...),
    profile=Depends(require_roles("approver_b")),
):
    """Run multimodal audit on the uploaded image for a content item."""
    img_bytes = await file.read()
    mime = file.content_type or "image/jpeg"
    return await audit_image_service(content_id, img_bytes, file.filename or "image.jpg", mime, profile)

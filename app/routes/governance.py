"""Content approval and governance workflow endpoints.

Manages content approval workflows with role-based access:
- Approvers: approve/reject content
- Creators: submit content, view inbox
- Both can view inbox

All business logic delegated to service layer.
"""
from fastapi import APIRouter, Depends, UploadFile, File
from pydantic import BaseModel
from typing import Optional

from app.core.auth import get_current_profile, require_roles
from app.services.governance import inbox, approve, reject, audit_image as audit_image_service

router = APIRouter(tags=["governance"])


class DecisionBody(BaseModel):
    """Request body for approve/reject decisions.

    Attributes:
        comment: Optional notes for decision rationale.
    """
    comment: Optional[str] = None


@router.get("/inbox")
async def inbox_endpoint(profile=Depends(get_current_profile)):
    """Get user's governance inbox (creator or approver view).

    Returns pending content for approval or created content status.

    Args:
        profile: Current user profile (role determines view).

    Returns:
        dict: {"items": list of pending content items}.
    """
    return {"items": inbox(profile)}


@router.post("/content/{content_id}/approve")
async def approve_endpoint(
    content_id: str, body: DecisionBody, profile=Depends(require_roles("approver_a", "approver_b"))
):
    """Approve a content item for publication.

    Requires approver_a or approver_b role.

    Args:
        content_id: Content identifier.
        body: Approval decision with optional comment.
        profile: Current user profile (role validated via Depends).

    Returns:
        dict: Updated content with approved status.

    Raises:
        HTTPException: 403 if insufficient role, 404 if not found.
    """
    return approve(content_id, body.comment, profile)


@router.post("/content/{content_id}/reject")
async def reject_endpoint(
    content_id: str, body: DecisionBody, profile=Depends(require_roles("approver_a", "approver_b"))
):
    """Reject a content item with feedback.

    Requires approver_a or approver_b role.

    Args:
        content_id: Content identifier.
        body: Rejection decision with comment (required).
        profile: Current user profile (role validated via Depends).

    Returns:
        dict: Updated content with rejected status and notes.

    Raises:
        HTTPException: 403 if insufficient role, 404 if not found.
    """
    return reject(content_id, body.comment, profile)


@router.post("/content/{content_id}/audit-image")
async def audit_image(
    content_id: str,
    file: UploadFile = File(...),
    profile=Depends(require_roles("approver_b")),
):
    """Audit content image for brand compliance during review.

    Uses brand visual guidelines to assess image violations.
    Results inform approval decision by approver_b.

    Requires approver_b role.

    Args:
        content_id: Content identifier containing this image.
        file: Image file to audit (JPEG, PNG, WebP, GIF, BMP).
        profile: Current user profile (must have approver_b role).

    Returns:
        dict: Audit results with violations and compliance verdict.

    Raises:
        HTTPException: 403 if insufficient role, 404 if content not found,
                      500 for vision model failures.
    """
    img_bytes = await file.read()
    mime = file.content_type or "image/jpeg"
    return await audit_image_service(content_id, img_bytes, file.filename or "image.jpg", mime, profile)

from fastapi import APIRouter, Depends, UploadFile, File

from app.core.auth import require_roles
from app.services.brand_audit import audit_brand_image as audit_brand_image_service

router = APIRouter(prefix="/brands", tags=["brand-audit"])


@router.post("/{brand_id}/audit-image")
async def audit_brand_image(
    brand_id: str,
    file: UploadFile = File(...),
    profile=Depends(require_roles("approver_b")),
):
    """Thin HTTP handler; all real work lives in ``app.services.brand_audit``."""

    img_bytes = await file.read()
    mime = file.content_type or "image/jpeg"
    return await audit_brand_image_service(
        brand_id, img_bytes, file.filename or "image.jpg", mime, profile
    )

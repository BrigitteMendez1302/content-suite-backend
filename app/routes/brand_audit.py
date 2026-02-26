"""Brand image compliance audit endpoints.

Audits images against brand visual guidelines using vision model (Google Gemini).
Performs semantic search for relevant guidelines, then applies multimodal rules.
Requires approver_b role for image audit permissions.
"""
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
    """Audit image compliance against brand visual guidelines.

    Workflow:
    1. Retrieve brand visual guidelines
    2. Generate embeddings for guidelines
    3. Upload image to Supabase Storage
    4. Call Gemini vision model with guidelines context
    5. Determine compliance verdict

    Requires approver_b role for security.

    Args:
        brand_id: Brand identifier.
        file: Image file to audit (JPEG, PNG, WebP, GIF, BMP).
        profile: Current user profile (must have approver_b role).

    Returns:
        dict: Audit results with violations, notes, and compliance status.

    Raises:
        HTTPException: 403 if insufficient role, 404 for invalid brand,
                      500 for vision model failures.
    """
    img_bytes = await file.read()
    mime = file.content_type or "image/jpeg"
    return await audit_brand_image_service(
        brand_id, img_bytes, file.filename or "image.jpg", mime, profile
    )

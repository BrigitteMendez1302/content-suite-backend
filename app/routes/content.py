"""Content generation endpoints.

Generates on-brand content using brand manuals and semantic search (RAG).
Content types include product descriptions, video scripts, and image prompts.
All business logic delegated to service layer.
"""
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Literal

from app.services.content import generate_content

router = APIRouter(prefix="/content", tags=["content"])


class GenerateRequest(BaseModel):
    """Request to generate on-brand content.

    Attributes:
        brand_id: Target brand identifier.
        type: Content type to generate.
        brief: Content brief/requirements.
    """
    brand_id: str
    type: Literal["product_description", "video_script", "image_prompt"]
    brief: str


@router.post("/generate")
async def generate(req: GenerateRequest):
    """Generate on-brand content using RAG with semantic search.

    Retrieves relevant manual sections via semantic similarity,
    reranks by content type, and generates content with Groq LLM.

    Args:
        req: Generation request with brand, content type, and brief.

    Returns:
        dict: Generated content with metadata (type, compliance notes, etc.).

    Raises:
        HTTPException: 400 for invalid brand/type, 500 for LLM failures.
    """
    return await generate_content(req)

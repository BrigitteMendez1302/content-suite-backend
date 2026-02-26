from fastapi import APIRouter
from pydantic import BaseModel
from typing import Literal

from app.services.content import generate_content

router = APIRouter(prefix="/content", tags=["content"])


class GenerateRequest(BaseModel):
    brand_id: str
    type: Literal["product_description", "video_script", "image_prompt"]
    brief: str


@router.post("/generate")
async def generate(req: GenerateRequest):
    """Thin HTTP handler; forward to the content service."""
    return await generate_content(req)

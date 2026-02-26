"""Pydantic models for brand management API endpoints."""
from pydantic import BaseModel


class BrandCreateRequest(BaseModel):
    """Request body for creating a new brand.

    Attributes:
        name: Brand name (e.g., "Acme Corp", "TechStart").
    """
    name: str


class BrandCreateResponse(BaseModel):
    """Response body for brand creation.

    Attributes:
        id: Auto-generated UUID for the brand.
        name: Brand name as provided in request.
    """
    id: str
    name: str
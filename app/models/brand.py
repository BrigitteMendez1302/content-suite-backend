from pydantic import BaseModel

class BrandCreateRequest(BaseModel):
    name: str

class BrandCreateResponse(BaseModel):
    id: str
    name: str
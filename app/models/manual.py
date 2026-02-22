from pydantic import BaseModel, Field
from typing import List, Dict, Any, Literal, Optional

class ToneModel(BaseModel):
    description: str
    dos: List[str] = Field(default_factory=list)
    donts: List[str] = Field(default_factory=list)

class MessagingModel(BaseModel):
    value_props: List[str] = Field(default_factory=list)
    taglines: List[str] = Field(default_factory=list)
    forbidden_claims: List[str] = Field(default_factory=list)
    preferred_terms: List[str] = Field(default_factory=list)
    forbidden_terms: List[str] = Field(default_factory=list)

class StyleRulesModel(BaseModel):
    reading_level: Literal["simple", "medium"] = "simple"
    length_guidelines: Dict[str, Any] = Field(default_factory=dict)

class VisualGuidelinesModel(BaseModel):
    colors: List[str] = Field(default_factory=list)
    logo_rules: List[str] = Field(default_factory=list)
    typography: List[str] = Field(default_factory=list)
    image_style: List[str] = Field(default_factory=list)
    notes: Optional[str] = None

class ExampleItem(BaseModel):
    type: str
    text: str
    why: Optional[str] = None

class ExamplesModel(BaseModel):
    good: List[ExampleItem] = Field(default_factory=list)
    bad: List[ExampleItem] = Field(default_factory=list)

class BrandManual(BaseModel):
    brand_name: str
    product: str
    audience: str
    tone: ToneModel
    messaging: MessagingModel
    style_rules: StyleRulesModel = Field(default_factory=StyleRulesModel)
    visual_guidelines: VisualGuidelinesModel = Field(default_factory=VisualGuidelinesModel)
    examples: ExamplesModel = Field(default_factory=ExamplesModel)
    approval_checklist: List[str] = Field(default_factory=list)
    assumptions: List[str] = Field(default_factory=list)
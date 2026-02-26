"""Pydantic models for brand manual data structures.

Brand manuals are comprehensive guidelines for creating on-brand content,
including tone, messaging, style rules, and visual guidelines validated
for type consistency.
"""
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Literal, Optional


class ToneModel(BaseModel):
    """Brand tone and voice guidelines.

    Attributes:
        description: How the brand communicates (e.g., "professional yet friendly").
        dos: Things to do when writing brand content.
        donts: Things to avoid in brand content.
    """
    description: str
    dos: List[str] = Field(default_factory=list)
    donts: List[str] = Field(default_factory=list)


class MessagingModel(BaseModel):
    """Core messaging framework for the brand.

    Attributes:
        value_props: Brand value propositions.
        taglines: Brand taglines and slogans.
        forbidden_claims: Claims that cannot be made.
        preferred_terms: Terminology to use (e.g., "AI" not "Artificial Intelligence").
        forbidden_terms: Terminology to avoid.
    """
    value_props: List[str] = Field(default_factory=list)
    taglines: List[str] = Field(default_factory=list)
    forbidden_claims: List[str] = Field(default_factory=list)
    preferred_terms: List[str] = Field(default_factory=list)
    forbidden_terms: List[str] = Field(default_factory=list)


class StyleRulesModel(BaseModel):
    """Writing style and formatting guidelines.

    Attributes:
        reading_level: "simple" for easy-to-read or "medium" for more complex.
        length_guidelines: Dict specifying content length preferences
                          (e.g., {"max_words": 100, "target": "80-100"}).
    """
    reading_level: Literal["simple", "medium"] = "simple"
    length_guidelines: Dict[str, Any] = Field(default_factory=dict)


class VisualGuidelinesModel(BaseModel):
    """Visual identity guidelines.

    Attributes:
        colors: Brand color palette descriptions.
        logo_rules: Guidelines for logo usage and placement.
        typography: Font families and hierarchy rules.
        image_style: Photography and image style guidelines.
        notes: Additional visual notes.
    """
    colors: List[str] = Field(default_factory=list)
    logo_rules: List[str] = Field(default_factory=list)
    typography: List[str] = Field(default_factory=list)
    image_style: List[str] = Field(default_factory=list)
    notes: Optional[str] = None


class ExampleItem(BaseModel):
    """Single example of good or bad brand content.

    Attributes:
        type: Category of example (e.g., "social media", "email subject").
        text: The example text.
        why: Explanation of why it's good/bad.
    """
    type: str
    text: str
    why: Optional[str] = None


class ExamplesModel(BaseModel):
    """Good and bad content examples.

    Attributes:
        good: List of examples to follow.
        bad: List of anti-patterns to avoid.
    """
    good: List[ExampleItem] = Field(default_factory=list)
    bad: List[ExampleItem] = Field(default_factory=list)


class BrandManual(BaseModel):
    """Complete brand manual for content guidance.

    Comprehensive guidelines covering brand identity, messaging strategy,
    writing style, visual standards, and content approval checklists.

    Attributes:
        brand_name: Name of the brand (e.g., "Acme Corp").
        product: Primary product or service category.
        audience: Target audience description and demographics.
        tone: Brand voice and communication style.
        messaging: Core messaging framework and terminology.
        style_rules: Writing style and formatting requirements.
        visual_guidelines: Brand visual identity rules.
        examples: Good/bad content examples for reference.
        approval_checklist: Items to verify before publishing content.
        assumptions: Contextual assumptions underlying this manual.
    """
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
"""Data models for the image generator."""
from typing import List, Optional, Dict, Any, Literal
from pydantic import BaseModel, Field, ConfigDict


class ColorConfig(BaseModel):
    """Color configuration for image generation."""

    primary: Optional[str] = None  # e.g., "#FF5733" or "blue"
    secondary: Optional[str] = None  # e.g., "#33FF57" or "green"


class SlideInput(BaseModel):
    """Input data for a single slide."""

    model_config = ConfigDict(populate_by_name=True)

    title: Optional[str] = None
    sources: Optional[List[Dict[str, str]]] = None
    image_keywords: Optional[List[str]] = Field(
        default=None,
        alias="ImageKeywords"
    )
    bullets: Optional[List[Dict[str, Any]]] = None

    # New parameters
    style: Optional[List[str]] = None  # e.g., ["minimal", "modern", "professional"]
    image_mode: Literal["stock_only", "ai_only", "auto"] = "auto"
    colors: Optional[ColorConfig] = None
    ai_model: Literal["auto", "flux", "banana", "imagen"] = "auto"


class KeywordExtractionResult(BaseModel):
    """Result from keyword extraction."""

    skip: bool = False
    topics_de: List[str] = []
    english_keywords: List[str] = []
    style: List[str] = []
    negative_keywords: List[str] = []
    constraints: Dict[str, Optional[str]] = {}


class ImageRef(BaseModel):
    """Reference to an image from a stock photo service."""

    index: int
    id: Optional[str]
    alt: Optional[str]
    regular_url: str
    full_url: str
    source: str  # "unsplash" or "pexels"
    photographer: Optional[str] = None
    photographer_url: Optional[str] = None


class QualityScore(BaseModel):
    """Quality assessment of an image."""

    quality_score: float
    presentation_score: Optional[float] = None
    is_safe: bool = True
    nudity_score: Optional[float] = None


class ScoredImage(BaseModel):
    """Image with quality scores."""

    image_ref: ImageRef
    scores: QualityScore


class ImageResult(BaseModel):
    """Final result containing image URL."""

    url: str
    source: str  # "stock" or "generated"
    keywords: str
    error: Optional[str] = None

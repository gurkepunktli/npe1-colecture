"""Data models for the image generator."""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel


class SlideInput(BaseModel):
    """Input data for a single slide."""

    title: str
    sources: Optional[List[Dict[str, str]]] = None
    unsplashSearchTerms: Optional[List[str]] = None
    bullets: Optional[List[Dict[str, Any]]] = None


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

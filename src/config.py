"""Configuration management for NPE1 Colecture."""
import os
from dotenv import load_dotenv
from pydantic import BaseModel
from typing import Optional

load_dotenv()


class Config(BaseModel):
    """Application configuration."""

    # API Keys
    openrouter_api_key: str = os.getenv("OPENROUTER_API_KEY", "")
    unsplash_access_key: str = os.getenv("UNSPLASH_ACCESS_KEY", "")
    pexels_api_key: str = os.getenv("PEXELS_API_KEY", "")
    sightengine_api_user: str = os.getenv("SIGHTENGINE_API_USER", "")
    sightengine_api_secret: str = os.getenv("SIGHTENGINE_API_SECRET", "")
    flux_api_key: str = os.getenv("FLUX_API_KEY", "")

    # Service URLs
    scoring_service_url: Optional[str] = os.getenv("SCORING_SERVICE_URL")

    # OpenRouter metadata (optional but recommended by OpenRouter)
    openrouter_referer: Optional[str] = os.getenv("OPENROUTER_REFERER")
    openrouter_title: Optional[str] = os.getenv("OPENROUTER_TITLE")

    # Quality thresholds
    min_presentation_score: float = float(os.getenv("MIN_PRESENTATION_SCORE", "0.6"))
    min_quality_score: float = float(os.getenv("MIN_QUALITY_SCORE", "0.7"))
    min_nudity_safe_score: float = float(os.getenv("MIN_NUDITY_SAFE_SCORE", "0.99"))

    # Model configurations
    gemini_model: str = "google/gemini-2.0-flash-001"
    claude_model: str = "anthropic/claude-3.5-haiku"
    flux_model: str = "flux-2-pro"
    gemini_image_model: str = "google/gemini-3-pro-image-preview"


config = Config()

"""FastAPI application for the image generator service."""
from pathlib import Path
from typing import Optional, List
from fastapi import FastAPI, HTTPException, Query, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .config import config
from .models import SlideInput, ImageResult, ColorConfig
from .orchestrator import ImageOrchestrator
from . import generated_cache

app = FastAPI(
    title="NPE1 Colecture Image Generator",
    description="AI-powered image finder and generator for PowerPoint presentations",
    version="1.0.0"
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static assets (e.g., error.png)
static_dir = Path(__file__).resolve().parent / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Initialize orchestrator
orchestrator = ImageOrchestrator()

# Log PUBLIC_BASE_URL for visibility at startup
print(f"[config] PUBLIC_BASE_URL={getattr(config, 'public_base_url', None)}")


@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "service": "NPE1 Colecture Image Generator",
        "status": "running",
        "version": "1.0.0"
    }


@app.post("/generate-image", response_model=ImageResult)
async def generate_image(slide: SlideInput):
    """
    Generate or find a suitable image for a slide.

    Args:
        slide: Slide content with title, keywords, and bullets

    Returns:
        Image result with URL and source information
    """
    try:
        result = await orchestrator.process_slide(slide)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/generate-image-simple", response_model=ImageResult)
async def generate_image_simple(
    title: Optional[str] = Query(None, description="Slide title (optional if keywords provided)"),
    style: Optional[str] = Query(None, description="Style value or scenario key (e.g., 'flat_illustration')"),
    image_mode: str = Query("auto", description="Image mode: stock_only, ai_only, or auto"),
    ai_model: str = Query("auto", description="AI model: auto/flux (both map to banana), banana/imagen, or google_banana"),
    primary_color: Optional[str] = Query(None, description="Primary color (e.g., '#0066CC' or 'blue')"),
    secondary_color: Optional[str] = Query(None, description="Secondary color"),
    keywords: Optional[str] = Query(None, description="Comma-separated keywords (overrides auto-extraction)")
):
    """
    Simple GET endpoint for image generation with query parameters.

    Example:
        GET /generate-image-simple?title=Digital%20Transformation&style=modern,minimal&image_mode=ai_only&ai_model=imagen
    """
    try:
        # Parse keywords
        keywords_list = None
        if keywords:
            keywords_list = [k.strip() for k in keywords.split(",")]

        # Build color config
        colors = None
        if primary_color or secondary_color:
            colors = ColorConfig(primary=primary_color, secondary=secondary_color)

        # Create SlideInput
        slide = SlideInput(
            title=title,
            style=style.strip() if style else None,
            image_mode=image_mode,  # type: ignore
            ai_model=ai_model,  # type: ignore
            colors=colors,
            image_keywords=keywords_list
        )

        result = await orchestrator.process_slide(slide)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/extract-keywords")
async def extract_keywords(slide: SlideInput):
    """
    Extract keywords from slide content.

    Args:
        slide: Slide content

    Returns:
        Extracted keywords
    """
    try:
        extraction_result, refined_keywords = orchestrator.keyword_extractor.extract_keywords(slide)
        return {
            "detailed": extraction_result.dict(),
            "refined": refined_keywords
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/generated/{image_id}")
async def get_generated_image(image_id: str):
    """Serve generated images stored in memory from data URLs."""
    cached = generated_cache.get_image(image_id)
    if not cached:
        raise HTTPException(status_code=404, detail="Image not found")
    return Response(content=cached.data, media_type=cached.media_type)

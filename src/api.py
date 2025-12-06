"""FastAPI application for the image generator service."""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .models import SlideInput, ImageResult
from .orchestrator import ImageOrchestrator

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

# Initialize orchestrator
orchestrator = ImageOrchestrator()


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

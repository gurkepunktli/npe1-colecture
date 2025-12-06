"""Main orchestration logic for image generation pipeline."""
from typing import Optional
from .models import SlideInput, ImageResult
from .keyword_extractor import KeywordExtractor
from .image_search import ImageSearcher
from .image_scorer import ImageScorer
from .image_generator import ImageGenerator


class ImageOrchestrator:
    """Orchestrates the complete image finding/generation pipeline."""

    def __init__(self):
        """Initialize the orchestrator."""
        self.keyword_extractor = KeywordExtractor()
        self.image_searcher = ImageSearcher()
        self.image_scorer = ImageScorer()
        self.image_generator = ImageGenerator()

    async def process_slide(self, slide: SlideInput) -> ImageResult:
        """
        Process a slide to find or generate a suitable image.

        Pipeline:
        1. Extract keywords from slide content
        2. Search stock photo services (Unsplash, Pexels)
        3. Score images for quality and presentation fit
        4. Return best image OR generate new one if none suitable

        Args:
            slide: Slide input data

        Returns:
            Image result with URL and metadata
        """
        print(f"Processing slide: {slide.title}")

        # Step 1: Extract keywords
        extraction_result, refined_keywords = self.keyword_extractor.extract_keywords(slide)
        print(f"Keywords: {refined_keywords}")

        if extraction_result.skip:
            print("Slide content not suitable for image generation")
            return ImageResult(
                url="",
                source="none",
                keywords=refined_keywords
            )

        # Step 2: Search for stock images
        print("Searching stock photo services...")
        search_results = await self.image_searcher.search_all(
            query=refined_keywords,
            per_page=10
        )
        print(f"Found {len(search_results)} images")

        if not search_results:
            # No images found - generate one
            return await self._generate_fallback_image(refined_keywords)

        # Step 3: Score images
        print("Scoring images...")
        scored_images = await self.image_scorer.score_images(
            search_results,
            topic=refined_keywords
        )

        # Step 4: Filter and sort
        suitable_images = self.image_scorer.filter_and_sort(scored_images)

        if suitable_images:
            # Return best matching stock image
            best_image = suitable_images[0]
            print(f"Selected stock image from {best_image.image_ref.source}")
            print(f"  Quality: {best_image.scores.quality_score:.2f}")
            print(f"  Presentation fit: {best_image.scores.presentation_score}")

            return ImageResult(
                url=best_image.image_ref.full_url,
                source=f"stock_{best_image.image_ref.source}",
                keywords=refined_keywords
            )
        else:
            # No suitable images - generate one
            print("No suitable stock images found, generating...")
            return await self._generate_fallback_image(refined_keywords)

    async def _generate_fallback_image(self, keywords: str) -> ImageResult:
        """
        Generate an image when no suitable stock photos are found.

        Args:
            keywords: Keywords for generation

        Returns:
            Image result with generated image URL
        """
        print(f"Generating image for: {keywords}")
        image_url = await self.image_generator.generate_from_keywords(keywords)

        if image_url:
            print(f"Generated image: {image_url}")
            return ImageResult(
                url=image_url,
                source="generated_flux",
                keywords=keywords
            )
        else:
            print("Image generation failed")
            return ImageResult(
                url="",
                source="failed",
                keywords=keywords
            )

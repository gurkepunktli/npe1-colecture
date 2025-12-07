"""Main orchestration logic for image generation pipeline."""
from typing import Optional
import httpx
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from .models import SlideInput, ImageResult
from .keyword_extractor import KeywordExtractor
from .image_search import ImageSearcher
from .image_scorer import ImageScorer
from .image_generator import ImageGenerator
from . import generated_cache
from .config import config


class ImageOrchestrator:
    """Orchestrates the complete image finding/generation pipeline."""

    def __init__(self):
        """Initialize the orchestrator."""
        self.keyword_extractor = KeywordExtractor()
        self.image_searcher = ImageSearcher()
        self.image_scorer = ImageScorer()
        self.image_generator = ImageGenerator()
        self.translator_llm = ChatOpenAI(
            model=config.gemini_model,
            openai_api_base="https://openrouter.ai/api/v1",
            openai_api_key=config.openrouter_api_key,
        )
        self.translation_prompt = ChatPromptTemplate.from_messages([
            ("system", "Translate the following text to English. Return only the translated text."),
            ("human", "{text}")
        ])

    async def process_slide(self, slide: SlideInput) -> ImageResult:
        """
        Process a slide to find or generate a suitable image.

        Pipeline:
        1. Extract keywords from slide content
        2. Search stock photo services (Unsplash, Pexels) OR skip if ai_only mode
        3. Score images for quality and presentation fit
        4. Return best image OR generate new one if none suitable

        Args:
            slide: Slide input data

        Returns:
            Image result with URL and metadata
        """
        print(f"Processing slide: {slide.title}")
        print(f"Image mode: {slide.image_mode}, AI model: {slide.ai_model}")

        slide = await self._ensure_english(slide)

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

        # If style enforces AI-only (scenario keys), skip stock search
        style_key = (slide.style or "").lower()
        if style_key in ("flat_illustration", "fine_line"):
            print(f"Style '{style_key}' forces AI generation, skipping stock search")
            return await self._generate_ai_image(slide, refined_keywords)

        # Check if AI-only mode
        if slide.image_mode == "ai_only":
            print("AI-only mode: Skipping stock photo search")
            return await self._generate_ai_image(slide, refined_keywords)

        # Step 2: Search for stock images (unless ai_only)
        print("Searching stock photo services...")
        search_results = await self.image_searcher.search_all(
            query=refined_keywords,
            per_page=10
        )
        print(f"Found {len(search_results)} images")

        # If stock_only mode and no results, return empty
        if not search_results and slide.image_mode == "stock_only":
            print("Stock-only mode: No images found")
            return ImageResult(
                url="",
                source="none",
                keywords=refined_keywords
            )

        if not search_results:
            # No images found - generate one (if auto mode)
            return await self._generate_ai_image(slide, refined_keywords)

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
            print(f"  URL: {best_image.image_ref.full_url}")

            return ImageResult(
                url=best_image.image_ref.full_url,
                source=f"stock_{best_image.image_ref.source}",
                keywords=refined_keywords
            )
        else:
            # No suitable images
            if slide.image_mode == "stock_only":
                print("Stock-only mode: No suitable images found")
                return ImageResult(
                    url="",
                    source="none",
                    keywords=refined_keywords
                )
            else:
                # Generate AI image as fallback
                print("No suitable stock images found, generating...")
                return await self._generate_ai_image(slide, refined_keywords)

    async def _generate_ai_image(self, slide: SlideInput, keywords: str) -> ImageResult:
        """
        Generate an AI image with slide configuration.

        Args:
            slide: Slide configuration (model, style, colors)
            keywords: Keywords for generation

        Returns:
            Image result with generated image URL
        """
        print(f"Generating image with {slide.ai_model} for: {keywords}")
        if slide.style:
            print(f"  Style: {slide.style}")
        if slide.colors:
            print(f"  Colors: primary={slide.colors.primary}, secondary={slide.colors.secondary}")

        # Select model: "banana" stays banana; "auto" defaults to flux; otherwise pass through.
        ai_model = slide.ai_model
        if ai_model == "auto":
            ai_model = "flux"

        image_url = await self.image_generator.generate_from_keywords(
            keywords=keywords,
            model=ai_model,
            style=slide.style,
            colors=slide.colors,
            slide=slide
        )

        base_url = config.public_base_url.rstrip("/") if getattr(config, "public_base_url", None) else "http://localhost:8080"

        if image_url:
            # If OpenRouter returned a data URL, store it and serve via /generated/{id}
            served_url = image_url
            if image_url.startswith("data:"):
                try:
                    image_id = generated_cache.store_data_url(image_url)
                    path = f"/generated/{image_id}"
                    served_url = f"{base_url}{path}"
                except Exception as exc:
                    print(f"Failed to cache data URL: {exc}")
            elif ai_model == "flux" and image_url.startswith("http"):
                # Download Flux image and serve via generated cache
                try:
                    async with httpx.AsyncClient(timeout=30.0) as client:
                        resp = await client.get(image_url)
                        resp.raise_for_status()
                        media_type = resp.headers.get("content-type", "application/octet-stream")
                        image_id = generated_cache.store_bytes(resp.content, media_type)
                        path = f"/generated/{image_id}"
                        served_url = f"{base_url}{path}"
                except Exception as exc:
                    print(f"Failed to download/cache Flux image: {exc}")

            # Nudity check for generated images (skip on errors/quotas)
            nudity_score = None
            try:
                nudity_data = await self.image_scorer.check_nudity_sightengine(served_url)
                nudity_score = nudity_data.get("suggestive_classes", {}).get("cleavage_categories", {}).get("none", 1.0)
                print(f"Nudity score for generated image: {nudity_score}")
            except Exception as exc:
                print(f"Nudity check skipped/failed: {exc}")

            # If unsafe, regenerate once with banana regardless of selected model
            if nudity_score is not None and nudity_score < config.min_nudity_safe_score:
                print("Generated image not safe enough, regenerating with banana")
                retry_url = await self.image_generator.generate_from_keywords(
                    keywords=keywords,
                    model="banana",
                    style=slide.style,
                    colors=slide.colors,
                    slide=slide
                )
                if retry_url:
                    served_url = retry_url
                    if retry_url.startswith("data:"):
                        try:
                            image_id = generated_cache.store_data_url(retry_url)
                            path = f"/generated/{image_id}"
                            served_url = f"{base_url}{path}"
                        except Exception as exc:
                            print(f"Failed to cache retry data URL: {exc}")
                    else:
                        # No download/cache for banana; return as is
                        served_url = retry_url
                    print(f"Regenerated image with banana: {served_url}")
                    source = "generated_banana"
                    return ImageResult(
                        url=served_url,
                        source=source,
                        keywords=keywords,
                        error=None
                    )
                else:
                    print("Retry generation with banana failed")

            print(f"Generated image: {served_url}")
            source = f"generated_{slide.ai_model}"
            return ImageResult(
                url=served_url,
                source=source,
                keywords=keywords,
                error=None
            )
        else:
            error_detail = self.image_generator.last_error or "Image generation failed"
            print(f"Image generation failed: {error_detail}")
            error_url = "/static/error.png"
            if getattr(config, "public_base_url", None):
                error_url = f"{config.public_base_url.rstrip('/')}{error_url}"
            return ImageResult(
                url=error_url,
                source="failed",
                keywords=keywords,
                error=error_detail
            )

    async def _ensure_english(self, slide: SlideInput) -> SlideInput:
        """
        Ensure title and bullets are in English; translate if needed.
        """
        try:
            texts = []
            if slide.title:
                texts.append(slide.title)
            if slide.bullets:
                texts.extend([b.get("bullet", "") for b in slide.bullets if b.get("bullet")])

            all_text = " ".join([t for t in texts if t]).strip().lower()
            if self._is_probably_english(all_text):
                return slide

            def translate_text(text: str) -> str:
                chain = self.translation_prompt | self.translator_llm | StrOutputParser()
                return chain.invoke({"text": text}).strip()

            new_title = translate_text(slide.title) if slide.title else None
            new_bullets = []
            if slide.bullets:
                for bullet in slide.bullets:
                    txt = bullet.get("bullet")
                    if txt:
                        bullet = bullet.copy()
                        bullet["bullet"] = translate_text(txt)
                    new_bullets.append(bullet)

            slide_dict = slide.model_dump()
            slide_dict["title"] = new_title
            slide_dict["bullets"] = new_bullets
            translated = SlideInput(**slide_dict)
            print("Translated slide content to English.")
            return translated
        except Exception as exc:
            print(f"Translation skipped due to error: {exc}")
            return slide

    def _is_probably_english(self, text: str) -> bool:
        """
        Heuristic check for English vs. German.
        """
        if not text:
            return True
        german_markers = [" und ", " der ", " die ", " das ", " mit ", " bitte", "zusammenfassung", "fragen"]
        umlauts = ["ä", "ö", "ü", "ß"]
        if any(c in text for c in umlauts):
            return False
        if any(marker in text for marker in german_markers):
            return False
        return True

"""Image quality and suitability scoring."""
import httpx
from typing import Optional
from langchain.prompts import ChatPromptTemplate
from langchain.schema.output_parser import StrOutputParser
from langchain_openai import ChatOpenAI

from .config import config
from .models import ImageRef, QualityScore, ScoredImage


class ImageScorer:
    """Scores images for quality and presentation suitability."""

    def __init__(self):
        """Initialize the image scorer."""
        self.llm = ChatOpenAI(
            model=config.gemini_model,
            openai_api_base="https://openrouter.ai/api/v1",
            openai_api_key=config.openrouter_api_key,
        )

    async def score_quality_sightengine(self, image_url: str) -> float:
        """
        Score image quality using SightEngine API.

        Args:
            image_url: URL of the image

        Returns:
            Quality score (0-1)
        """
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://api.sightengine.com/1.0/check.json",
                params={
                    "models": "quality",
                    "api_user": config.sightengine_api_user,
                    "api_secret": config.sightengine_api_secret,
                    "url": image_url
                }
            )
            response.raise_for_status()
            data = response.json()

        return data.get("quality", {}).get("score", 0.0)

    async def check_nudity_sightengine(self, image_url: str) -> dict:
        """
        Check image for nudity/inappropriate content using SightEngine.

        Args:
            image_url: URL of the image

        Returns:
            Nudity check results
        """
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://api.sightengine.com/1.0/check.json",
                params={
                    "models": "nudity-2.1",
                    "api_user": config.sightengine_api_user,
                    "api_secret": config.sightengine_api_secret,
                    "url": image_url
                }
            )
            response.raise_for_status()
            data = response.json()

        return data.get("nudity", {})

    async def score_presentation_fit(
        self,
        image_url: str,
        topic: str
    ) -> Optional[float]:
        """
        Score image fit for presentation topic using local scoring service.

        Args:
            image_url: URL of the image
            topic: Topic/keywords to match

        Returns:
            Presentation fit score (0-1) or None if service unavailable
        """
        if not config.scoring_service_url:
            return None

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{config.scoring_service_url}/score",
                    json={"image_url": image_url, "topic": topic},
                    headers={"Content-Type": "application/json"}
                )
                response.raise_for_status()
                data = response.json()

            return data.get("presentation_score", 0.5)
        except Exception as e:
            print(f"Presentation scoring failed: {e}")
            return None

    async def score_image(
        self,
        image_ref: ImageRef,
        topic: str
    ) -> ScoredImage:
        """
        Score an image comprehensively.

        Args:
            image_ref: Image reference
            topic: Topic to match against

        Returns:
            Scored image with all quality metrics
        """
        import asyncio

        # Run scoring tasks in parallel
        quality_task = self.score_quality_sightengine(image_ref.regular_url)
        presentation_task = self.score_presentation_fit(image_ref.regular_url, topic)
        nudity_task = self.check_nudity_sightengine(image_ref.regular_url)

        quality_score, presentation_score, nudity_data = await asyncio.gather(
            quality_task, presentation_task, nudity_task,
            return_exceptions=True
        )

        # Handle exceptions
        if isinstance(quality_score, Exception):
            print(f"Quality scoring failed: {quality_score}")
            quality_score = 0.5

        if isinstance(presentation_score, Exception):
            presentation_score = None

        if isinstance(nudity_data, Exception):
            print(f"Nudity check failed: {nudity_data}")
            nudity_data = {}

        # Check if image is safe (no inappropriate content)
        nudity_safe_score = nudity_data.get(
            "suggestive_classes", {}
        ).get("cleavage_categories", {}).get("none", 1.0)

        is_safe = nudity_safe_score >= config.min_nudity_safe_score

        scores = QualityScore(
            quality_score=quality_score,
            presentation_score=presentation_score,
            is_safe=is_safe,
            nudity_score=nudity_safe_score
        )

        return ScoredImage(image_ref=image_ref, scores=scores)

    async def score_images(
        self,
        images: list[ImageRef],
        topic: str
    ) -> list[ScoredImage]:
        """
        Score multiple images.

        Args:
            images: List of image references
            topic: Topic to match against

        Returns:
            List of scored images
        """
        import asyncio

        tasks = [self.score_image(img, topic) for img in images]
        return await asyncio.gather(*tasks)

    def filter_and_sort(
        self,
        scored_images: list[ScoredImage]
    ) -> list[ScoredImage]:
        """
        Filter images by quality thresholds and sort by score.

        Args:
            scored_images: List of scored images

        Returns:
            Filtered and sorted images
        """
        # Filter by thresholds
        filtered = []
        for scored_img in scored_images:
            if not scored_img.scores.is_safe:
                continue

            if scored_img.scores.quality_score < config.min_quality_score:
                continue

            if scored_img.scores.presentation_score is not None:
                if scored_img.scores.presentation_score < config.min_presentation_score:
                    continue

            filtered.append(scored_img)

        # Sort by presentation score (primary) and quality score (secondary)
        filtered.sort(
            key=lambda x: (
                x.scores.presentation_score or 0,
                x.scores.quality_score
            ),
            reverse=True
        )

        return filtered

"""Image quality and suitability scoring."""
import logging
import httpx
from typing import Optional, Any
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_openai import ChatOpenAI

from .config import config
from .models import ImageRef, QualityScore, ScoredImage


class ImageScorer:
    """Scores images for quality and presentation suitability."""

    def __init__(self):
        """Initialize the image scorer."""
        self.logger = logging.getLogger(__name__)
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

        quality_score = data.get("quality", {}).get("score", 0.0)
        self.logger.info("Sightengine quality: url=%s score=%.3f", image_url, quality_score)

        return quality_score

    async def check_nudity_sightengine(self, image_url: str) -> dict:
        """
        Check image for nudity/inappropriate content using SightEngine.

        Args:
            image_url: URL of the image

        Returns:
            Nudity check results
        """
        async with httpx.AsyncClient() as client:
            try:
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
            except httpx.HTTPStatusError as exc:
                body = exc.response.text[:200] if exc.response is not None else ""
                msg = body.lower()
                if "daily usage limit" in msg:
                    self.logger.warning(
                        "Sightengine nudity skipped (quota): status=%s body=%s",
                        exc.response.status_code if exc.response else "n/a",
                        body,
                    )
                    return {}
                raise

        nudity_data = data.get("nudity", {})
        self.logger.info(
            "Sightengine nudity: url=%s raw=%s",
            image_url,
            nudity_data
        )

        return nudity_data

    async def check_nudity_local(self, image_url: str) -> dict:
        """
        Check image for nudity using the local analyzer service.

        Args:
            image_url: URL of the image

        Returns:
            Nudity check results from the local service
        """
        if not config.nudity_service_url:
            raise RuntimeError("NUDITY_SERVICE_URL not configured")

        endpoint = config.nudity_service_url.rstrip("/")
        if not endpoint.endswith("/analyze"):
            endpoint = f"{endpoint}/analyze"

        async with httpx.AsyncClient(timeout=60.0) as client:
            payload = {"image_url": image_url}
            # Service accepts threshold/model as form fields (curl -F), not query params
            if config.nudity_service_threshold is not None:
                payload["threshold"] = str(config.nudity_service_threshold)
            if config.nudity_service_model:
                payload["clip_model"] = config.nudity_service_model

            response = await client.post(
                endpoint,
                data=payload
            )
            response.raise_for_status()
            data = response.json()

        self.logger.info("Local nudity check: url=%s raw=%s", image_url, data)
        return data

    async def check_nudity(self, image_url: str) -> dict:
        """
        Check image for nudity, preferring local analyzer and falling back to SightEngine.

        Args:
            image_url: URL of the image

        Returns:
            Nudity check results
        """
        local_error: Optional[Exception] = None

        if config.nudity_service_url:
            try:
                return await self.check_nudity_local(image_url)
            except Exception as exc:
                local_error = exc
                self.logger.warning(
                    "Local nudity check failed, falling back to SightEngine: %s",
                    exc
                )

        try:
            return await self.check_nudity_sightengine(image_url)
        except Exception as exc:
            if local_error:
                raise RuntimeError(
                    f"Local nudity service failed ({local_error}); SightEngine fallback failed ({exc})"
                ) from exc
            raise

    def extract_nudity_safe_score(self, nudity_data: dict) -> float:
        """
        Derive a safety score (1.0 is safest) from local or SightEngine responses.
        """
        if not nudity_data:
            return 1.0

        def clamp(value: Any) -> Optional[float]:
            try:
                num = float(value)
            except (TypeError, ValueError):
                return None
            return max(0.0, min(1.0, num))

        # Handle nested payloads
        nested_result = nudity_data.get("result")
        if isinstance(nested_result, dict):
            return self.extract_nudity_safe_score(nested_result)

        predictions = nudity_data.get("predictions")
        if isinstance(predictions, list) and predictions:
            first_prediction = predictions[0]
            if isinstance(first_prediction, dict):
                return self.extract_nudity_safe_score(first_prediction)

        # Local service variants
        for key in ("safe_score", "safe_prob", "safe_probability"):
            candidate = clamp(nudity_data.get(key))
            if candidate is not None:
                return candidate

        safe_flag = nudity_data.get("safe")
        if isinstance(safe_flag, bool):
            return 1.0 if safe_flag else 0.0

        if "nsfw_score" in nudity_data:
            raw_nsfw = clamp(nudity_data.get("nsfw_score"))
            if raw_nsfw is not None:
                return 1.0 - raw_nsfw

        nsfw_flag = nudity_data.get("nsfw")
        if isinstance(nsfw_flag, bool):
            return 0.0 if nsfw_flag else 1.0

        unsafe_flag = nudity_data.get("unsafe")
        if isinstance(unsafe_flag, bool):
            return 0.0 if unsafe_flag else 1.0

        label = nudity_data.get("label")
        score_candidate = clamp(nudity_data.get("score"))
        if isinstance(label, str) and score_candidate is not None:
            label_lower = label.lower()
            if label_lower in ("nsfw", "unsafe", "porn"):
                return 1.0 - score_candidate
            if label_lower in ("sfw", "safe"):
                return score_candidate

        # SightEngine structure
        sightengine_score = nudity_data.get(
            "suggestive_classes", {}
        ).get("cleavage_categories", {}).get("none")
        candidate = clamp(sightengine_score)
        if candidate is not None:
            return candidate

        return 1.0

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
            self.logger.info("Presentation scoring skipped (no SCORING_SERVICE_URL)")
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

            presentation_score = data.get("presentation_score", 0.5)
            self.logger.info(
                "Presentation score: url=%s topic=%s score=%.3f",
                image_url,
                topic,
                presentation_score
            )
            return presentation_score
        except Exception as e:
            self.logger.warning("Presentation scoring failed: %s", e)
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
        nudity_task = self.check_nudity(image_ref.regular_url)

        quality_score, presentation_score, nudity_data = await asyncio.gather(
            quality_task, presentation_task, nudity_task,
            return_exceptions=True
        )

        # Handle exceptions
        if isinstance(quality_score, Exception):
            msg = str(quality_score).lower()
            if "daily usage limit" in msg:
                self.logger.warning("Quality scoring skipped (quota): %s", quality_score)
                quality_score = config.min_quality_score
            else:
                self.logger.warning("Quality scoring failed: %s", quality_score)
                quality_score = 0.5

        if isinstance(presentation_score, Exception):
            presentation_score = None

        if isinstance(nudity_data, Exception):
            self.logger.warning("Nudity check failed: %s", nudity_data)
            nudity_data = {}

        # Check if image is safe (no inappropriate content)
        nudity_safe_score = self.extract_nudity_safe_score(nudity_data)

        is_safe = nudity_safe_score >= config.min_nudity_safe_score

        scores = QualityScore(
            quality_score=quality_score,
            presentation_score=presentation_score,
            is_safe=is_safe,
            nudity_score=nudity_safe_score
        )

        # Ensure per-image scoring is visible even without logging configuration
        print(
            f"[Score] source={image_ref.source} id={image_ref.id or 'n/a'} "
            f"quality={scores.quality_score:.3f} "
            f"presentation={scores.presentation_score if scores.presentation_score is not None else 'None'} "
            f"nudity_safe={scores.nudity_score if scores.nudity_score is not None else 'n/a'} "
            f"is_safe={scores.is_safe}"
        )
        self.logger.info(
            "Scored image %s (source=%s): quality=%.3f, presentation=%s, nudity_safe=%.3f, is_safe=%s",
            image_ref.id or image_ref.full_url,
            image_ref.source,
            scores.quality_score,
            f"{scores.presentation_score:.3f}" if scores.presentation_score is not None else "None",
            scores.nudity_score if scores.nudity_score is not None else -1,
            scores.is_safe,
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

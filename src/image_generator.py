"""AI image generation using FLUX or Google Imagen."""
import httpx
import asyncio
import json
from typing import Optional, Literal
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_openai import ChatOpenAI

from .config import config
from .models import ColorConfig, SlideInput
from .prompts import SCENARIO_PROMPTS, GENERATION_PROMPT_SYSTEM, NEGATIVE_PROMPT


class ImageGenerator:
    """Generates images using AI when stock photos do not match."""

    def __init__(self):
        """Initialize the image generator."""
        self.last_error: Optional[str] = None
        self.llm = ChatOpenAI(
            model=config.claude_model,
            openai_api_base="https://openrouter.ai/api/v1",
            openai_api_key=config.openrouter_api_key,
        )

        self.prompt_template = ChatPromptTemplate.from_messages([
            ("system", GENERATION_PROMPT_SYSTEM),
            ("human", "Keywords: {keywords}")
        ])

    def _select_scenario(self, style: Optional[str]) -> Optional[str]:
        """Pick a scenario key if present in style string."""
        if not style:
            return None
        key = style.lower().strip()
        if key in SCENARIO_PROMPTS:
            return key
        return None

    async def create_generation_prompt(
        self,
        keywords: str,
        style: Optional[str] = None,
        colors: Optional[ColorConfig] = None,
        slide: Optional[SlideInput] = None
    ) -> str:
        """
        Create an image generation prompt from keywords, style, and colors.

        Args:
            keywords: Keywords describing the desired image
            style: Style attribute or scenario key (e.g., "minimal" or "flat_illustration")
            colors: Primary and secondary colors
            slide: Slide payload (for scenario-driven prompting)

        Returns:
            Generated prompt for image generation
        """
        self.last_error = None
        try:
            scenario = self._select_scenario(style)
            if scenario:
                slide_payload = slide.model_dump() if slide else {"keywords": keywords}
                prompt_template = ChatPromptTemplate.from_messages([
                    ("system", SCENARIO_PROMPTS[scenario]),
                    ("human", "{slide_json}")
                ])
                chain = prompt_template | self.llm | StrOutputParser()
                prompt = await chain.ainvoke({"slide_json": json.dumps(slide_payload)})
                return prompt.strip()

            # Build style instruction
            style_instruction = ""
            if style:
                style_instruction = f"Style-Anforderungen: {style}"

            # Build color instruction
            color_instruction = ""
            if colors:
                color_parts = []
                if colors.primary:
                    color_parts.append(f"Primary color: {colors.primary}")
                if colors.secondary:
                    color_parts.append(f"Secondary color: {colors.secondary}")
                if color_parts:
                    color_instruction = "Farbanforderungen: " + ", ".join(color_parts)

            chain = self.prompt_template | self.llm | StrOutputParser()
            prompt = await chain.ainvoke({
                "keywords": keywords,
                "style_instruction": style_instruction,
                "color_instruction": color_instruction
            })
            return prompt.strip()
        except Exception as e:
            self.last_error = f"Prompt generation failed: {e}"
            raise

    async def generate_with_flux(
        self,
        prompt: str,
        width: int = 1024,
        height: int = 1024
    ) -> Optional[str]:
        """
        Generate an image using FLUX API.

        Args:
            prompt: Text prompt for generation
            width: Image width
            height: Image height

        Returns:
            URL of generated image or None if failed
        """
        try:
            self.last_error = None
            endpoint = f"https://api.eu.bfl.ai/v1/{config.flux_model}"
            async with httpx.AsyncClient(timeout=150.0) as client:
                # Submit generation request
                response = await client.post(
                    endpoint,
                    headers={
                        "Content-Type": "application/json",
                        "x-key": config.flux_api_key
                    },
                    json={
                        "prompt": f"{prompt}. Keinen Text im Bild generieren.",
                        "width": width,
                        "height": height,
                        "steps": 28,
                        "guidance": 3,
                        "safety_tolerance": 2,
                        "output_format": "jpeg"
                    }
                )
                print(f"[Flux] submit url={endpoint} status={response.status_code}")
                submit_body = response.text[:500] if hasattr(response, "text") else ""
                if submit_body:
                    print(f"[Flux] submit body (trunc): {submit_body}")
                response.raise_for_status()
                data = response.json()

                polling_url = data.get("polling_url")
                if not polling_url:
                    return None

                # Wait for generation to complete
                await asyncio.sleep(20)

                # Poll for result
                for attempt in range(20):
                    poll_response = await client.get(polling_url)
                    print(f"[Flux] poll attempt={attempt+1} status={poll_response.status_code}")
                    poll_text = poll_response.text[:500] if hasattr(poll_response, "text") else ""
                    if poll_text:
                        print(f"[Flux] poll body (trunc): {poll_text}")
                    poll_response.raise_for_status()
                    poll_data = poll_response.json()

                    status = poll_data.get("status")

                    # Some Flux responses use "Ready" instead of "succeeded" and put the URL under result.sample
                    if status in ("succeeded", "Ready"):
                        result = poll_data.get("result", {}) or {}
                        sample_url = result.get("sample") or poll_data.get("sample")
                        if sample_url:
                            return sample_url
                        # Fallback: return whatever URL is available
                        return None
                    elif status == "failed":
                        return None

                    await asyncio.sleep(4)

                return None

        except Exception as e:
            msg = f"FLUX generation failed: {e}"
            self.last_error = msg
            print(msg)
            return None

    async def generate_with_imagen(
        self,
        prompt: str,
        width: int = 1024,
        height: int = 1024
    ) -> Optional[str]:
        """
        Generate an image using Gemini image preview via OpenRouter (chat/completions).

        Args:
            prompt: Text prompt for generation
            width: Image width (unused by OpenRouter chat endpoint, kept for parity)
            height: Image height (unused by OpenRouter chat endpoint, kept for parity)

        Returns:
            URL of generated image or None if failed
        """
        try:
            self.last_error = None
            headers = {
                "Authorization": f"Bearer {config.openrouter_api_key}",
                "Content-Type": "application/json"
            }

            # Optional but recommended by OpenRouter for compliance/analytics
            if config.openrouter_referer:
                headers["HTTP-Referer"] = config.openrouter_referer
            if config.openrouter_title:
                headers["X-Title"] = config.openrouter_title

            payload = {
                "model": config.gemini_image_model,
                "messages": [
                    {"role": "user", "content": prompt}
                ],
                "modalities": ["image", "text"]
            }

            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers=headers,
                    json=payload
                )
                response.raise_for_status()

                try:
                    data = response.json()
                except Exception:
                    text = response.text[:500]
                    self.last_error = f"OpenRouter JSON parse failed (status {response.status_code}): {text}"
                    return None

                choices = data.get("choices") or []
                if not choices:
                    self.last_error = f"No choices in OpenRouter response: {data}"
                    return None

                message = choices[0].get("message", {}) or {}
                images = message.get("images") or []
                if images:
                    first_image = images[0] or {}
                    image_url = (first_image.get("image_url") or {}).get("url")
                    if image_url:
                        return image_url

                self.last_error = f"No image returned by OpenRouter: {data}"
                return None

        except Exception as e:
            msg = f"Gemini image generation failed: {e}"
            self.last_error = msg
            print(msg)
            return None

    async def generate_image(
        self,
        prompt: str,
        model: Literal["auto", "flux", "banana", "imagen"] = "auto",
        width: int = 1024,
        height: int = 1024
    ) -> Optional[str]:
        """
        Generate an image using specified AI model.

        Args:
            prompt: Text prompt for generation
            model: AI model to use ("flux" or "imagen")
            width: Image width
            height: Image height

        Returns:
            URL of generated image or None if failed
        """
        self.last_error = None
        if model in ("auto", "flux"):
            return await self.generate_with_flux(prompt, width, height)
        elif model in ("banana", "imagen"):
            return await self.generate_with_imagen(prompt, width, height)
        else:
            print(f"Unknown model: {model}")
            self.last_error = f"Unknown model: {model}"
            return None

    async def generate_from_keywords(
        self,
        keywords: str,
        model: Literal["auto", "flux", "banana", "imagen"] = "auto",
        style: Optional[str] = None,
        colors: Optional[ColorConfig] = None,
        width: int = 1024,
        height: int = 1024,
        slide: Optional[SlideInput] = None
    ) -> Optional[str]:
        """
        Generate image from keywords with style and color support.

        Args:
            keywords: Keywords describing the desired image
            model: AI model to use ("flux" or "imagen")
            style: Style attributes
            colors: Color configuration
            width: Image width
            height: Image height
            slide: Slide payload (used for scenario prompts)

        Returns:
            URL of generated image or None if failed
        """
        self.last_error = None
        prompt = await self.create_generation_prompt(keywords, style, colors, slide)
        final_prompt = f"{prompt} {NEGATIVE_PROMPT}".strip()
        print(f"Generated prompt for {model}: {final_prompt}")
        url = await self.generate_image(final_prompt, model, width, height)
        if url is None and self.last_error is None:
            self.last_error = "Image generation returned no result"
        return url

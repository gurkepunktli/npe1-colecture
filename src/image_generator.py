"""AI image generation using FLUX or Google Imagen."""
import httpx
import asyncio
from typing import Optional, List, Literal
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_openai import ChatOpenAI

from .config import config
from .models import ColorConfig


class ImageGenerator:
    """Generates images using AI when stock photos don't match."""

    def __init__(self):
        """Initialize the image generator."""
        self.llm = ChatOpenAI(
            model=config.claude_model,
            openai_api_base="https://openrouter.ai/api/v1",
            openai_api_key=config.openrouter_api_key,
        )

        self.prompt_template = ChatPromptTemplate.from_messages([
            ("system", """Erstelle basierend auf Keywords, Style und optionalen Farben einen Prompt aus einem Satz, um daraus ein passendes Bild zu generieren.

Beachte, dass es für PowerPoint-Folie geeignet sein muss. Also keine Fotos, die nur für den privaten Bereich geeignet sind.

{style_instruction}
{color_instruction}

Antworte mit genau einem Satz."""),
            ("human", "Keywords: {keywords}")
        ])

    async def create_generation_prompt(
        self,
        keywords: str,
        style: Optional[List[str]] = None,
        colors: Optional[ColorConfig] = None
    ) -> str:
        """
        Create an image generation prompt from keywords, style, and colors.

        Args:
            keywords: Keywords describing the desired image
            style: Style attributes (e.g., ["minimal", "modern"])
            colors: Primary and secondary colors

        Returns:
            Generated prompt for image generation
        """
        # Build style instruction
        style_instruction = ""
        if style:
            style_str = ", ".join(style)
            style_instruction = f"Style-Anforderungen: {style_str}"

        # Build color instruction
        color_instruction = ""
        if colors:
            color_parts = []
            if colors.primary:
                color_parts.append(f"Primärfarbe: {colors.primary}")
            if colors.secondary:
                color_parts.append(f"Sekundärfarbe: {colors.secondary}")
            if color_parts:
                color_instruction = "Farbanforderungen: " + ", ".join(color_parts)

        chain = self.prompt_template | self.llm | StrOutputParser()
        prompt = await chain.ainvoke({
            "keywords": keywords,
            "style_instruction": style_instruction,
            "color_instruction": color_instruction
        })
        return prompt.strip()

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
            async with httpx.AsyncClient(timeout=120.0) as client:
                # Submit generation request
                response = await client.post(
                    "https://api.bfl.ai/v1/flux-2-pro",
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
                response.raise_for_status()
                data = response.json()

                polling_url = data.get("polling_url")
                if not polling_url:
                    return None

                # Wait for generation to complete
                await asyncio.sleep(15)

                # Poll for result
                for attempt in range(10):
                    poll_response = await client.get(polling_url)
                    poll_response.raise_for_status()
                    poll_data = poll_response.json()

                    status = poll_data.get("status")
                    if status == "succeeded":
                        result = poll_data.get("result", {})
                        return result.get("sample")
                    elif status == "failed":
                        return None

                    await asyncio.sleep(3)

                return None

        except Exception as e:
            print(f"FLUX generation failed: {e}")
            return None

    async def generate_with_imagen(
        self,
        prompt: str,
        width: int = 1024,
        height: int = 1024
    ) -> Optional[str]:
        """
        Generate an image using Google Imagen via OpenRouter.

        Args:
            prompt: Text prompt for generation
            width: Image width
            height: Image height

        Returns:
            URL of generated image or None if failed
        """
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(
                    "https://openrouter.ai/api/v1/images/generations",
                    headers={
                        "Authorization": f"Bearer {config.openrouter_api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": "google/imagen-3.0-generate-001",
                        "prompt": f"{prompt}. No text in image.",
                        "n": 1,
                        "size": f"{width}x{height}"
                    }
                )
                response.raise_for_status()
                data = response.json()

                # OpenRouter returns image URL directly
                if data.get("data") and len(data["data"]) > 0:
                    return data["data"][0].get("url")

                return None

        except Exception as e:
            print(f"Imagen generation failed: {e}")
            return None

    async def generate_image(
        self,
        prompt: str,
        model: Literal["flux", "imagen"] = "flux",
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
        if model == "flux":
            return await self.generate_with_flux(prompt, width, height)
        elif model == "imagen":
            return await self.generate_with_imagen(prompt, width, height)
        else:
            print(f"Unknown model: {model}")
            return None

    async def generate_from_keywords(
        self,
        keywords: str,
        model: Literal["flux", "imagen"] = "flux",
        style: Optional[List[str]] = None,
        colors: Optional[ColorConfig] = None,
        width: int = 1024,
        height: int = 1024
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

        Returns:
            URL of generated image or None if failed
        """
        prompt = await self.create_generation_prompt(keywords, style, colors)
        print(f"Generated prompt for {model}: {prompt}")
        return await self.generate_image(prompt, model, width, height)

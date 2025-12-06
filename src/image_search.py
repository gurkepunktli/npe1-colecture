"""Image search across stock photo services."""
import httpx
from typing import List, Dict, Any
from .config import config
from .models import ImageRef


class ImageSearcher:
    """Searches for images on Unsplash and Pexels."""

    def __init__(self):
        """Initialize the image searcher."""
        self.unsplash_headers = {
            "Authorization": f"Client-ID {config.unsplash_access_key}"
        }
        self.pexels_headers = {
            "Authorization": config.pexels_api_key
        }

    async def search_unsplash(self, query: str, per_page: int = 10) -> List[ImageRef]:
        """
        Search for images on Unsplash.

        Args:
            query: Search query
            per_page: Number of results

        Returns:
            List of image references
        """
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://api.unsplash.com/search/photos",
                headers=self.unsplash_headers,
                params={"query": query, "per_page": per_page}
            )
            response.raise_for_status()
            data = response.json()

        results = []
        for idx, photo in enumerate(data.get("results", [])):
            results.append(ImageRef(
                index=idx,
                id=photo.get("id"),
                alt=photo.get("alt_description") or photo.get("description"),
                regular_url=photo["urls"].get("regular") or photo["urls"].get("full"),
                full_url=photo["urls"].get("full") or photo["urls"].get("raw"),
                source="unsplash",
                photographer=photo.get("user", {}).get("name"),
                photographer_url=photo.get("user", {}).get("links", {}).get("html")
            ))

        return results

    async def search_pexels(self, query: str, per_page: int = 10) -> List[ImageRef]:
        """
        Search for images on Pexels.

        Args:
            query: Search query
            per_page: Number of results

        Returns:
            List of image references
        """
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://api.pexels.com/v1/search",
                headers=self.pexels_headers,
                params={"query": query, "per_page": per_page}
            )
            response.raise_for_status()
            data = response.json()

        results = []
        for idx, photo in enumerate(data.get("photos", [])):
            results.append(ImageRef(
                index=idx,
                id=str(photo.get("id")),
                alt=photo.get("alt"),
                regular_url=photo["src"].get("large2x") or photo["src"].get("large"),
                full_url=photo["src"].get("original") or photo["src"].get("large2x"),
                source="pexels",
                photographer=photo.get("photographer"),
                photographer_url=photo.get("photographer_url")
            ))

        return results

    async def search_all(self, query: str, per_page: int = 10) -> List[ImageRef]:
        """
        Search both Unsplash and Pexels.

        Args:
            query: Search query
            per_page: Number of results per service

        Returns:
            Combined and deduplicated list of image references
        """
        import asyncio

        unsplash_task = self.search_unsplash(query, per_page)
        pexels_task = self.search_pexels(query, per_page)

        unsplash_results, pexels_results = await asyncio.gather(
            unsplash_task, pexels_task, return_exceptions=True
        )

        # Handle exceptions
        if isinstance(unsplash_results, Exception):
            print(f"Unsplash search failed: {unsplash_results}")
            unsplash_results = []

        if isinstance(pexels_results, Exception):
            print(f"Pexels search failed: {pexels_results}")
            pexels_results = []

        # Combine and deduplicate
        all_results = []
        seen_urls = set()

        for result in unsplash_results + pexels_results:
            key = f"{result.source}:{result.id}" if result.id else result.full_url
            if key not in seen_urls:
                seen_urls.add(key)
                result.index = len(all_results)
                all_results.append(result)

        return all_results

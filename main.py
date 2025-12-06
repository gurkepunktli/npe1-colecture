"""Main entry point for the application."""
import asyncio
from src.models import SlideInput
from src.orchestrator import ImageOrchestrator


async def main():
    """Run a test example."""
    orchestrator = ImageOrchestrator()

    # Example slide
    slide = SlideInput(
        title="Lean Production: Eine Einführung",
        unsplashSearchTerms=["lean manufacturing", "industrial efficiency", "business transformation"],
        bullets=[
            {"bullet": "Intellektueller Ansatz für Wettbewerbsfähigkeit.", "sub": []},
            {"bullet": "System von Maßnahmen und Methoden.", "sub": []},
            {"bullet": "Ursprung: \"MIT-Studie\" und japanische Herausforderung.", "sub": []}
        ]
    )

    print("=" * 80)
    print("NPE1 Colecture - Image Generator Test")
    print("=" * 80)

    result = await orchestrator.process_slide(slide)

    print("\n" + "=" * 80)
    print("RESULT:")
    print(f"  URL: {result.url}")
    print(f"  Source: {result.source}")
    print(f"  Keywords: {result.keywords}")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())

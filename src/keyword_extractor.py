"""Keyword extraction using LangChain and LLMs."""
import json
from typing import Optional
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_openai import ChatOpenAI

from .config import config
from .models import SlideInput, KeywordExtractionResult


class KeywordExtractor:
    """Extracts keywords from slide text for image search."""

    def __init__(self):
        """Initialize the keyword extractor."""
        self.llm = ChatOpenAI(
            model=config.gemini_model,
            openai_api_base="https://openrouter.ai/api/v1",
            openai_api_key=config.openrouter_api_key,
        )

        self.extraction_prompt = ChatPromptTemplate.from_messages([
            ("system", """Du extrahierst aus Folientexten bildrelevante Stockfoto-Keywords.
Regeln:
- Keine Marken, Namen, vertrauliche Daten, Zahlen-/IDs ohne Bildbezug.
- Erzeuge generische, visuelle Begriffe auf EN (z. B. "teamwork", "data analytics").
- Fokussiere auf Motiv, Szene, Objekt, Stimmung, Umgebung.
- Wenn Text unbrauchbar (Agenda, reiner Zahlenmix), liefere "skip": true und leere Listen.
Output: NUR valides JSON mit Schluesseln in dieser Reihenfolge:
{{
 "skip": boolean,
 "topics_de": string[],         // 3-6 kurze deutsche Themen
 "english_keywords": string[],  // 10-15 suchoptimierte Begriffe (EN, klein)
 "style": string[],             // 2-4 (z. B. "minimal", "isometric", "aerial")
 "negative_keywords": string[], // 5-10 (z. B. "text","watermark","logo","diagram","screenshot")
 "constraints": {{ "orientation": "landscape"|"portrait"|"square", "color": string|null }}
}}
Pruefe, dass alle Werte arrays ohne Duplikate sind; entferne Fuellwoerter."""),
            ("human", "{text}")
        ])

        self.refinement_prompt = ChatPromptTemplate.from_messages([
            ("system", """Extrahiere die wichtigsten Keywords und reduziere auf 2-3 Stück auf Englisch.

Hintergrund: Suche nach Keywords für passende Bilder auf Folien von PowerPoint.

Antwort mit 2-3 Keywords. Bspw. "Hund, Wiese", nicht mehr. Es muss genau so geantwortet werden!"""),
            ("human", "Sämtliche gefundene Keywords: {keywords}")
        ])

    def extract_keywords(self, slide: SlideInput) -> tuple[KeywordExtractionResult, str]:
        """
        Extract keywords from slide content.

        Args:
            slide: Slide input data

        Returns:
            Tuple of (detailed extraction result, refined keywords string)
        """
        # If keywords were explicitly provided, skip LLM extraction/refinement
        if slide.unsplashSearchTerms:
            explicit_keywords = [k for k in slide.unsplashSearchTerms if k]
            extraction_obj = KeywordExtractionResult(
                skip=False,
                english_keywords=explicit_keywords,
                topics_de=[],
                style=[],
                negative_keywords=[],
                constraints={}
            )
            refined_keywords = ", ".join(explicit_keywords[:3]) if explicit_keywords else ""
            return extraction_obj, refined_keywords

        # Build text from slide (title is optional)
        text_parts = []
        if slide.title:
            text_parts.append(slide.title)
        if slide.bullets:
            for bullet in slide.bullets:
                text_parts.append(bullet.get("bullet", ""))

        text = " ".join([part for part in text_parts if part]).strip()

        # Step 1: Extract detailed keywords
        extraction_chain = self.extraction_prompt | self.llm | StrOutputParser()
        extraction_result = extraction_chain.invoke({"text": text})

        try:
            extracted_data = json.loads(extraction_result)
            extraction_obj = KeywordExtractionResult(**extracted_data)
        except (json.JSONDecodeError, Exception):
            # Fallback to simple extraction
            extraction_obj = KeywordExtractionResult(
                skip=False,
                english_keywords=slide.unsplashSearchTerms or [],
            )

        # Step 2: Refine to 2-3 most important keywords
        all_keywords = ", ".join(extraction_obj.english_keywords)
        refinement_chain = self.refinement_prompt | self.llm | StrOutputParser()
        refined_keywords = refinement_chain.invoke({"keywords": all_keywords})

        return extraction_obj, refined_keywords.strip()

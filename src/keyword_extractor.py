"""Keyword extraction using LangChain and LLMs."""
import json
from typing import Optional
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_openai import ChatOpenAI

from .config import config
from .models import SlideInput, KeywordExtractionResult
from .prompts import KEYWORD_EXTRACTION_PROMPT, KEYWORD_REFINEMENT_PROMPT


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
            ("system", KEYWORD_EXTRACTION_PROMPT),
            ("human", "{text}")
        ])

        self.refinement_prompt = ChatPromptTemplate.from_messages([
            ("system", KEYWORD_REFINEMENT_PROMPT),
            ("human", "All found keywords: {keywords}")
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

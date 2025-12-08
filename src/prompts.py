"""Prompt blocks used across scenarios."""

from typing import TypedDict


class ScenarioConfig(TypedDict):
    """Configuration for a single scenario (e.g., flat_illustration, fine_line, photorealistic).

    Attributes:
        content_prompt_instructions: System prompt that instructs the LLM how to convert
                                    slide JSON into a content description
        style_prompt: Visual style requirements to append to the content prompt
        layout_prompt: Layout and composition requirements (background, spacing, aspect ratio)
        negative_prompt: Elements to avoid in the generated image
    """
    content_prompt_instructions: str
    style_prompt: str
    layout_prompt: str
    negative_prompt: str


# ============================================================================
# SCENARIO CONFIGURATIONS
# ============================================================================
# Each scenario defines all prompt components needed for image generation:
# 1. content_prompt_instructions: How to extract content from slide JSON
# 2. style_prompt: Visual style requirements
# 3. layout_prompt: Composition and background requirements
# 4. negative_prompt: Elements to avoid
# ============================================================================

SCENARIO_CONFIGS: dict[str, ScenarioConfig] = {
    # ------------------------------------------------------------------------
    # FLAT ILLUSTRATION
    # ------------------------------------------------------------------------
    "flat_illustration": {
        "content_prompt_instructions": """You are an assistant that converts slide JSON into a concise English "content prompt" for an image generation model.

Goal:
From the JSON description of a lecture slide, create a short textual description of what should be visible in an illustration that supports the main idea of the slide. This text will later be combined with separate style, layout and negative prompt blocks.

Input:
- You will receive a single JSON object that represents one slide.
- The JSON may contain fields such as:
  - "title"
  - "body_blocks" (with bullet points or text)
  - "speaker_notes"
  - "plain_text_summary"
  - "metadata" (e.g. topic, course, difficulty, language)
- Text in the JSON may be in German or another language.

Your task:
1. Understand the core concept of the slide using the available fields, in this priority:
   - If "plain_text_summary" is present and non-empty, use it as the primary source.
   - Otherwise, combine "title", "body_blocks" and "speaker_notes" to infer the main idea.
2. Choose a simple, didactic visual interpretation that would help students understand this idea. Reasonable options include:
   - a small scene with 1-3 people or key objects,
   - a simple process or cycle with a few steps,
   - an abstract metaphor or symbolic representation.
   Choose one that fits the content best, but keep the image concept simple and uncluttered.
3. Write a short English description (about 1-3 sentences) of what should be visible in the image:
   - Mention that it is for a university lecture slide about the topic.
   - Describe only the semantic content: who or what is visible, what they are doing, and how this supports the concept of the slide.
   - Focus on the main elements; avoid unnecessary small details.

Important constraints:
- Output only the content description, as plain English prose. Do not return JSON, lists, bullet points or explanations.
- Do not mention any visual style or medium. Avoid words like: flat, vector, line art, sketch, photorealistic, 3D, watercolor, oil painting, pixel art, comic, anime, etc.
- Do not mention colours, lighting, aspect ratio, resolution, background colour, or composition terms like "16:9", "white background", "high resolution", "4k", "centered composition".
- Do not include any negative instructions such as "no text", "no logo", "no watermark", "no clutter".
- Do not reference the JSON or field names in your output.
- Always write in natural, fluent English, even if the input JSON is in German.
- The output must be exactly one paragraph of one to three sentences.

Output:
- Return only the final content prompt as a single paragraph of English text, nothing else.""",

        "style_prompt": """In a modern flat vector illustration style, professional yet friendly, with soft rounded shapes, minimal details and smooth solid colours, using a limited colour palette based on #125456 and #F2C945.""",

        "layout_prompt": """Very light background softly tinted towards #F9F8F7, 16:9 aspect ratio, plenty of white space around the main elements.""",

        "negative_prompt": """No text, no lettering, no captions, no watermarks, no logos, no brands, no cluttered background, no noisy textures, no heavy gradients, no ultra-realistic rendering beyond the chosen style, no strong shadows, no dark background, no crowded scene, no user interface screenshots, no specific or labelled diagrams or frameworks such as Scrum boards or official process charts, only abstract or generic shapes to suggest processes."""
    },

    # ------------------------------------------------------------------------
    # FINE LINE
    # ------------------------------------------------------------------------
    "fine_line": {
        "content_prompt_instructions": """You are an assistant that converts slide JSON into a concise English "content prompt" for an image generation model.

Goal:
From the JSON description of a lecture slide, create a short textual description of what should be visible in an illustration that supports the main idea of the slide. This text will later be combined with separate style, layout and negative prompt blocks.

Input:
- You will receive a single JSON object that represents one slide.
- The JSON may contain fields such as:
  - "title"
  - "body_blocks" (with bullet points or text)
  - "speaker_notes"
  - "plain_text_summary"
  - "metadata" (e.g. topic, course, difficulty, language)
- Text in the JSON may be in German or another language.

Your task:
1. Understand the core concept of the slide using the available fields, in this priority:
   - If "plain_text_summary" is present and non-empty, use it as the primary source.
   - Otherwise, combine "title", "body_blocks" and "speaker_notes" to infer the main idea.
2. Choose a simple, didactic visual interpretation that would help students understand this idea. Reasonable options include:
   - a small scene with 1-3 people or key objects,
   - a simple process or cycle with a few steps,
   - an abstract metaphor or symbolic representation.
   Choose one that fits the content best, but keep the image concept simple and uncluttered.
3. Write a short English description (about 1-3 sentences) of what should be visible in the image:
   - Mention that it is for a university lecture slide about the topic.
   - Describe only the semantic content: who or what is visible, what they are doing, and how this supports the concept of the slide.
   - Focus on the main elements; avoid unnecessary small details.

Important constraints:
- Output only the content description, as plain English prose. Do not return JSON, lists, bullet points or explanations.
- Do not mention any visual style or medium. Avoid words like: flat, vector, line art, sketch, photorealistic, 3D, watercolor, oil painting, pixel art, comic, anime, etc.
- Do not mention colours, lighting, aspect ratio, resolution, background colour, or composition terms like "16:9", "white background", "high resolution", "4k", "centered composition".
- Do not include any negative instructions such as "no text", "no logo", "no watermark", "no clutter".
- Do not reference the JSON or field names in your output.
- Always write in natural, fluent English, even if the input JSON is in German.
- The output must be exactly one paragraph of one to three sentences.

Output:
- Return only the final content prompt as a single paragraph of English text, nothing else.""",

        "style_prompt": """In a clean fine-line illustration style with thin consistent outlines, mostly line art with only very subtle flat colour accents, very minimal details, using #125456 and #F2C945 sparingly.""",

        "layout_prompt": """Very light background softly tinted towards #F9F8F7, 16:9 aspect ratio, plenty of white space around the main elements.""",

        "negative_prompt": """No text, no lettering, no captions, no watermarks, no logos, no brands, no cluttered background, no noisy textures, no heavy gradients, no ultra-realistic rendering beyond the chosen style, no strong shadows, no dark background, no crowded scene, no user interface screenshots, no specific or labelled diagrams or frameworks such as Scrum boards or official process charts, only abstract or generic shapes to suggest processes."""
    },

    # ------------------------------------------------------------------------
    # PHOTOREALISTIC
    # ------------------------------------------------------------------------
    "photorealistic": {
        "content_prompt_instructions": """You are an assistant that converts slide JSON into a concise English "content prompt" for an image generation model.

Goal:
From the JSON description of a lecture slide, create a short textual description of what should be visible in an illustration that supports the main idea of the slide. This text will later be combined with separate style, layout and negative prompt blocks.

Input:
- You will receive a single JSON object that represents one slide.
- The JSON may contain fields such as:
  - "title"
  - "body_blocks" (with bullet points or text)
  - "speaker_notes"
  - "plain_text_summary"
  - "metadata" (e.g. topic, course, difficulty, language)
- Text in the JSON may be in German or another language.

Your task:
1. Understand the core concept of the slide using the available fields, in this priority:
   - If "plain_text_summary" is present and non-empty, use it as the primary source.
   - Otherwise, combine "title", "body_blocks" and "speaker_notes" to infer the main idea.
2. Choose a simple, didactic visual interpretation that would help students understand this idea. Reasonable options include:
   - a small scene with 1-3 people or key objects,
   - a simple process or cycle with a few steps,
   - an abstract metaphor or symbolic representation.
   Choose one that fits the content best, but keep the image concept simple and uncluttered.
3. Write a short English description (about 1-3 sentences) of what should be visible in the image:
   - Mention that it is for a university lecture slide about the topic.
   - Describe only the semantic content: who or what is visible, what they are doing, and how this supports the concept of the slide.
   - Focus on the main elements; avoid unnecessary small details.

Important constraints:
- Output only the content description, as plain English prose. Do not return JSON, lists, bullet points or explanations.
- Do not mention any visual style or medium. Avoid words like: flat, vector, line art, sketch, photorealistic, 3D, watercolor, oil painting, pixel art, comic, anime, etc.
- Do not mention colours, lighting, aspect ratio, resolution, background colour, or composition terms like "16:9", "white background", "high resolution", "4k", "centered composition".
- Do not include any negative instructions such as "no text", "no logo", "no watermark", "no clutter".
- Do not reference the JSON or field names in your output.
- Always write in natural, fluent English, even if the input JSON is in German.
- The output must be exactly one paragraph of one to three sentences.

Output:
- Return only the final content prompt as a single paragraph of English text, nothing else.""",

        "style_prompt": """In a clean, high-quality photorealistic style with neutral, studio-like lighting, low noise, calm, slightly desaturated colour palette based on #125456 and #F2C945, resembling a professional stock photo suitable for presentation slides.""",

        "layout_prompt": """Very light background softly tinted towards #F9F8F7, 16:9 aspect ratio, plenty of white space around the main elements.""",

        "negative_prompt": """No text, no lettering, no captions, no watermarks, no logos, no brands, no cluttered background, no noisy textures, no heavy gradients, no ultra-realistic rendering beyond the chosen style, no strong shadows, no dark background, no crowded scene, no user interface screenshots, no specific or labelled diagrams or frameworks such as Scrum boards or official process charts, only abstract or generic shapes to suggest processes."""
    }
}


# ============================================================================
# LEGACY COMPATIBILITY
# ============================================================================
# Keep SCENARIO_PROMPTS for backward compatibility, but map to new structure
SCENARIO_PROMPTS = {
    key: config["content_prompt_instructions"]
    for key, config in SCENARIO_CONFIGS.items()
}

GENERATION_PROMPT_SYSTEM = """Create a single-sentence prompt from keywords, style, and optional colors to generate a fitting image.

Ensure the image is appropriate for a PowerPoint slide; avoid anything only suitable for private use.

{style_instruction}
{color_instruction}

Answer with exactly one sentence."""

KEYWORD_EXTRACTION_PROMPT = """You extract stock-photo-relevant keywords from slide text.
Rules:
- No brands, names, confidential data, or numeric IDs without visual meaning.
- Produce generic, visual English terms (e.g., "teamwork", "data analytics").
- Focus on subject, scene, objects, mood, environment.
- If the text is unusable (agenda, pure numbers), return "skip": true and empty lists.
Output: ONLY valid JSON with keys in this order:
{
 "skip": boolean,
 "topics_de": string[],         // 3-6 short German topics
 "english_keywords": string[],  // 10-15 search-optimized terms (EN, lowercase)
 "style": string[],             // 2-4 (e.g., "minimal", "isometric", "aerial")
 "negative_keywords": string[], // 5-10 (e.g., "text","watermark","logo","diagram","screenshot")
 "constraints": { "orientation": "landscape"|"portrait"|"square", "color": string|null }
}
Validate all values are arrays without duplicates; remove filler words."""

KEYWORD_REFINEMENT_PROMPT = """Extract the most important keywords and reduce to 2-3 in English.

Background: Searching for keywords to find suitable images for PowerPoint slides.

Answer with exactly 2-3 keywords, nothing more."""

# ============================================================================
# GLOBAL FALLBACK (for non-scenario modes)
# ============================================================================
# This is used when no specific scenario is selected (e.g., generic keyword mode)
NEGATIVE_PROMPT = (
    "Negative prompt: No text, no lettering, no captions, no watermarks, no logos, "
    "no brands, no cluttered background, no noisy textures, no heavy gradients, "
    "no ultra-realistic rendering beyond the chosen style, no strong shadows, "
    "no dark background, no crowded scene, no user interface screenshots, "
    "no specific or labelled diagrams or frameworks such as Scrum boards or official process charts, "
    "only abstract or generic shapes to suggest processes."
)

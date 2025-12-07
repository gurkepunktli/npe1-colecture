# NPE1 Colecture – Image Generator

AI-powered image finder and generator for PowerPoint slides. Takes slide text, extracts visual keywords, searches stock photos, scores quality and safety, and falls back to AI image generation when needed.

## Overview
- Pipeline: Keywords extrahieren -> Unsplash/Pexels suchen -> Qualitaet/Safety/Praesentationsfit scoren -> ggf. KI-Bild generieren (Flux oder Gemini Image Preview via OpenRouter) -> bestes Bild liefern.
- FastAPI-Service mit Swagger UI (`/docs`).
- LLM via OpenRouter (Gemini/Claude); Safety/Qualitaet via SightEngine; optional Presentation-Scoring-Service.

## API Keys
| Service | Env Var | Zweck |
|---------|---------|-------|
| OpenRouter | `OPENROUTER_API_KEY` | LLM-Zugriff (Gemini/Claude, auch Gemini Image Preview) |
| Unsplash | `UNSPLASH_ACCESS_KEY` | Stock-Suche |
| Pexels | `PEXELS_API_KEY` | Stock-Suche |
| SightEngine | `SIGHTENGINE_API_USER`, `SIGHTENGINE_API_SECRET` | Qualitaet + Nudity/Safety |
| FLUX | `FLUX_API_KEY` | KI-Bildgenerierung (Flux) |

Optional: `SCORING_SERVICE_URL`, `MIN_PRESENTATION_SCORE`, `MIN_QUALITY_SCORE`, `MIN_NUDITY_SAFE_SCORE`, `PUBLIC_BASE_URL`, `OPENROUTER_REFERER`, `OPENROUTER_TITLE`, `FLUX_MODEL` (z. B. `flux-2-pro`, `flux-2-flex`).

## Setup
- **Local (Python)**: `python -m venv venv && venv\Scripts\activate` → `pip install -r requirements.txt` → `.env` aus `.env.example` füllen → `python run_server.py` (http://localhost:8080).
- **Docker Compose**: `.env` füllen → `docker-compose up -d` → Logs `docker-compose logs -f` → Stop `docker-compose down`.
- **Portainer**: Stack aus Repo `https://github.com/gurkepunktli/npe1-colecture`, Compose `docker-compose.yml`, Env Vars setzen, Deploy.

## API Usage

### POST /generate-image (JSON)
```json
{
  "title": "Digital Transformation",
  "bullets": [
    {"bullet": "Cloud migration and SaaS adoption"},
    {"bullet": "AI integration in business processes"}
  ],
  "ImageKeywords": ["technology", "innovation"],   // optional, überschreibt Auto-Extraktion
  "style": "flat_illustration",                    // Stil oder Szenario-Key
  "image_mode": "auto",                            // stock_only | ai_only | auto
  "ai_model": "auto",                              // auto (=flux), flux, banana/imagen
  "colors": { "primary": "#0066CC", "secondary": "#00CC66" }
}
```

### GET /generate-image-simple (Query)
```
/generate-image-simple?title=Digital+Transformation&style=flat_illustration&image_mode=ai_only&ai_model=auto&primary_color=%230066CC&secondary_color=%2300CC66&keywords=technology,innovation
```

### Fields (POST /generate-image)
- `title` (string) – Folientitel
- `bullets` (array) – optional, Bullet-Points
- `ImageKeywords` (array) – optional, explizite Keywords (überschreibt Auto-Extraktion)
- `style` (string) – optional, kann auch Szenario-Keys enthalten (`flat_illustration`, `fine_line`, `photorealistic`)
- `image_mode` – `stock_only` | `ai_only` | `auto` (Default)
- `ai_model` – `auto` (=flux), `flux`, `imagen/banana` (Default: auto)
- `colors` (object) – optional, z. B. `{ "primary": "#0066CC", "secondary": "#00CC66" }`

### Image modes & sources
- Modes: `stock_only` (nur Stock), `ai_only` (direkt KI), `auto` (Stock, dann KI-Fallback)
- Response `source`: `stock_unsplash`, `stock_pexels`, `generated_flux`, `generated_imagen`, `none`, `failed`

## Architecture
- `src/config.py` – Konfiguration/Env
- `src/models.py` – Pydantic-Modelle
- `src/keyword_extractor.py` – LangChain LLM-Extraktion
- `src/image_search.py` – Unsplash/Pexels
- `src/image_scorer.py` – Qualitaet/Safety/Presentation Scoring
- `src/image_generator.py` – Flux/Gemini Image Preview
- `src/orchestrator.py` – Pipeline-Steuerung
- `src/api.py` – FastAPI-Endpunkte
- `src/generated_cache.py` – In-Memory Cache fuer data:-Bilder / gecachte Downloads

## Troubleshooting
- 401/403 bei Stock: Unsplash/Pexels Keys prüfen.
- Leere/failed: Logs checken, Schwellen senken, optionalen Presentation-Scoring-Service entfernen.
- KI ohne Bild: Flux/Gemini-Key prüfen; bei `data:`-Antworten `PUBLIC_BASE_URL` setzen; bei Flux-Polling Logs anschauen (Submit/Poll Status).

## License
TBD

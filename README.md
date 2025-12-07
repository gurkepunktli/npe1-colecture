# NPE1 Colecture - Image Generator

AI-powered image finder and generator for PowerPoint slides. Takes slide text, extracts visual keywords, searches stock photos, scores quality and safety, and falls back to AI image generation when needed.

## Was das System macht
- Pipeline: Keywords extrahieren -> Unsplash/Pexels suchen -> Qualitaet/Safety/Praesentationsfit scoren -> ggf. KI-Bild generieren (Flux oder Gemini Image Preview via OpenRouter) -> bestes Bild liefern.
- FastAPI-Service mit automatischer Swagger UI.
- LLM-Aufrufe laufen ueber OpenRouter (Gemini/Claude); Safety/Qualitaet via SightEngine; optionaler Presentation-Scoring-Service.

## Features
- Keyword-Extraktion (Gemini/Claude) mit Skip-Logic fuer ungeeignete Slides.
- Multi-Source-Suche (Unsplash, Pexels) inkl. Deduplizierung.
- Scoring: technische Qualitaet, Nudity/Safety, optional Praesentationsfit; Schwellwerte konfigurierbar.
- KI-Bildgenerierung als Fallback (Flux oder Gemini Image Preview).
- REST-API + vereinfachter GET-Endpunkt fuer schnelle Tests.

## Voraussetzungen / API Keys
| Service | Env Var | Zweck |
|---------|---------|-------|
| OpenRouter | `OPENROUTER_API_KEY` | LLM-Zugriff (Gemini/Claude, auch fuer Gemini Image Preview) |
| Unsplash | `UNSPLASH_ACCESS_KEY` | Stock-Suche |
| Pexels | `PEXELS_API_KEY` | Stock-Suche |
| SightEngine | `SIGHTENGINE_API_USER`, `SIGHTENGINE_API_SECRET` | Qualitaet + Nudity/Safety |
| FLUX | `FLUX_API_KEY` | KI-Bildgenerierung (Flux) |

Optional:
- `SCORING_SERVICE_URL` - eigener Service fuer Praesentationsfit-Score
- `MIN_PRESENTATION_SCORE` (Default 0.6), `MIN_QUALITY_SCORE` (0.7), `MIN_NUDITY_SAFE_SCORE` (0.99)
- `PUBLIC_BASE_URL` - Basis-URL fuer ausgelieferte, gecachte data:-Bilder
- `OPENROUTER_REFERER`, `OPENROUTER_TITLE` - von OpenRouter empfohlen
- `FLUX_MODEL` - Flux-Endpunkt-Pfad, Default `flux-2-pro` (z. B. `flux-2-flex`, `flux-kontext-pro`, `flux-pro-1.1-ultra`, `flux-pro-1.1`, `flux-pro`, `flux-dev`)

## Setup

### Lokale Entwicklung (Python)
1) Virtualenv: `python -m venv venv && venv\Scripts\activate` (PowerShell)  
2) Dependencies: `pip install -r requirements.txt`  
3) Env: `cp .env.example .env` und Keys eintragen  
4) Start: `python run_server.py` -> http://localhost:8080

### Docker Compose (Dev)
1) `.env` anlegen und fuellen (`cp .env.example .env`).  
2) Start: `docker-compose up -d`  
3) Logs: `docker-compose logs -f`  
4) Stop: `docker-compose down`

### Portainer (Prod)
Kurzfassung (Details in `PORTAINER.md`):
1) Portainer -> Stacks -> Add stack  
2) Repository: `https://github.com/gurkepunktli/npe1-colecture`, Compose path: `docker-compose.yml`  
3) Environment Variables setzen (Keys s. oben)  
4) Deploy, Logs pruefen, Port 8080 testen

## Nutzung der API

### POST /generate-image
Minimalbeispiel:
```bash
curl -X POST http://localhost:8080/generate-image \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Digital Transformation",
    "bullets": [{"bullet": "Cloud Migration"}, {"bullet": "AI Integration"}],
    "style": ["modern", "minimal"],
    "image_mode": "auto",
    "ai_model": "flux"
  }'
```

### GET /generate-image-simple
Beispiel:
```
GET /generate-image-simple?title=Digital+Transformation&style=modern,minimal&image_mode=ai_only&ai_model=flux&primary_color=%230066CC&secondary_color=%2300CC66
```

### POST /extract-keywords
Liefert detaillierte und verfeinerte Keywords zur Kontrolle.

### Image Modes
- `stock_only`: nur Stock-Fotos, keine KI
- `ai_only`: direkt KI, keine Stock-Suche
- `auto` (Default): Stock bevorzugt, KI als Fallback

### Moegliche `source` Werte im Response
- `stock_unsplash`, `stock_pexels`
- `generated_flux`, `generated_imagen`
- `none` (nichts Passendes gefunden, stock_only)
- `failed` (Generierung fehlgeschlagen)

## Architektur (Kurzueberblick)
- `src/config.py` - Konfiguration/Env
- `src/models.py` - Pydantic-Modelle
- `src/keyword_extractor.py` - LangChain LLM-Extraktion
- `src/image_search.py` - Unsplash/Pexels
- `src/image_scorer.py` - Qualitaet/Safety/Presentation Scoring
- `src/image_generator.py` - Flux/Gemini Image Preview
- `src/orchestrator.py` - Pipeline-Steuerung
- `src/api.py` - FastAPI-Endpunkte
- `src/generated_cache.py` - In-Memory Cache fuer data:-Bilder

## Troubleshooting
- 401/403 bei Stock-Suche: API Keys fuer Unsplash/Pexels pruefen.
- Leere oder failed-Responses: Logs checken, Qualitaets-Schwellen ggf. senken, optionalen Presentation-Scoring-Service deaktivieren (`SCORING_SERVICE_URL` entfernen).
- KI-Generierung ohne Bild: Flux/Gemini-Key pruefen; bei `data:`-Antworten `PUBLIC_BASE_URL` setzen, falls die API extern erreichbar sein soll.

## License
TBD

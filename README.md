# NPE1 Colecture - Image Generator

**AI-powered image finder and generator for PowerPoint presentations**

Automatisierte Bildfindung für PowerPoint-Präsentationen mit intelligenter Keyword-Extraktion, Multi-Source-Suche und KI-generierter Fallback-Lösung.

## Funktionsweise

Das System durchläuft einen mehrstufigen Pipeline-Prozess:

1. **Keyword-Extraktion**: LLMs analysieren Folientitel und Inhalt, um relevante visuelle Suchbegriffe zu generieren
2. **Multi-Source-Suche**: Parallele Suche in Unsplash und Pexels Stock-Photo-Datenbanken
3. **Quality Scoring**: Automatische Bewertung von Bildqualität, Präsentationseignung und Safety-Checks
4. **KI-Generierung**: Falls keine passenden Stock-Fotos gefunden werden, generiert FLUX AI ein maßgeschneidertes Bild
5. **Best Match Selection**: Auswahl des am besten bewerteten Bildes basierend auf konfigurierbaren Qualitätsschwellenwerten

## Features

- **Intelligente Keyword-Extraktion**: Verwendet Gemini/Claude über OpenRouter zur Extraktion präsentationsrelevanter Keywords
- **Multi-Source Image Search**: Gleichzeitige Suche in Unsplash und Pexels mit Deduplizierung
- **Quality Scoring**:
  - Technische Bildqualität via SightEngine API
  - Optional: Semantische Präsentationseignung via Custom Scoring Service
  - NSFW/Safety-Filterung
- **KI-Bildgenerierung**: FLUX AI als Fallback für fehlende Stock-Fotos
- **REST API**: FastAPI-Server mit automatischer Swagger-Dokumentation
- **Docker-Ready**: Containerisiert für einfaches Deployment mit Portainer

## API Keys erforderlich

Die folgenden API-Keys müssen konfiguriert werden:

### Pflichtfelder

| Service | Variable | Beschreibung | Bezugsquelle |
|---------|----------|--------------|--------------|
| **OpenRouter** | `OPENROUTER_API_KEY` | LLM-Zugriff für Gemini & Claude | https://openrouter.ai/ |
| **Unsplash** | `UNSPLASH_ACCESS_KEY` | Stock-Foto-Suche | https://unsplash.com/developers |
| **Pexels** | `PEXELS_API_KEY` | Stock-Foto-Suche | https://www.pexels.com/api/ |
| **SightEngine** | `SIGHTENGINE_API_USER`<br>`SIGHTENGINE_API_SECRET` | Bildqualität & Safety-Checks | https://sightengine.com/ |
| **FLUX** | `FLUX_API_KEY` | KI-Bildgenerierung | https://api.bfl.ai/ |

### Optional

| Variable | Default | Beschreibung |
|----------|---------|--------------|
| `SCORING_SERVICE_URL` | - | URL eines Custom Scoring Service für semantische Präsentationseignung |
| `MIN_PRESENTATION_SCORE` | 0.6 | Minimale Präsentationseignung (0-1) |
| `MIN_QUALITY_SCORE` | 0.7 | Minimale Bildqualität (0-1) |
| `MIN_NUDITY_SAFE_SCORE` | 0.99 | Minimaler Safety-Score (0-1) |

## Konfiguration der API-Keys

### Für Portainer Deployment (Empfohlen)

Die API-Keys werden **direkt in Portainer** als Stack Environment Variables konfiguriert:

1. Portainer → Stacks → Add stack
2. Repository: `https://github.com/gurkepunktli/npe1-colecture`
3. **Environment Variables** Tab → Jede Variable einzeln hinzufügen:
   ```
   OPENROUTER_API_KEY=sk-or-...
   UNSPLASH_ACCESS_KEY=...
   PEXELS_API_KEY=...
   SIGHTENGINE_API_USER=...
   SIGHTENGINE_API_SECRET=...
   FLUX_API_KEY=...
   ```
4. Deploy

**Wichtig**: Die Datei `stack.env` im Repository enthält nur Platzhalter. Die echten Werte werden von Portainer eingefügt.

### Für lokale Entwicklung

Erstelle eine `.env` Datei im Projektverzeichnis:

```bash
cp .env.example .env
```

Bearbeite `.env` und füge die API-Keys ein:

```env
OPENROUTER_API_KEY=sk-or-v1-...
UNSPLASH_ACCESS_KEY=...
PEXELS_API_KEY=...
SIGHTENGINE_API_USER=...
SIGHTENGINE_API_SECRET=...
FLUX_API_KEY=...
```

## Deployment & Nutzung

### Portainer (Production)

**Voraussetzungen:**
- Portainer Installation mit Zugriff auf Docker
- Externes Netzwerk `cloudflare_net` muss existieren (oder in docker-compose.yml anpassen)
- Alle API-Keys vorbereitet (siehe oben)

**Deployment-Schritte:**

1. **Stack erstellen** in Portainer:
   - Portainer → Stacks → Add stack
   - Name: `npe1-colecture`
   - Build method: **Repository**

2. **Repository konfigurieren**:
   - Repository URL: `https://github.com/gurkepunktli/npe1-colecture`
   - Repository reference: `refs/heads/main`
   - Compose path: `docker-compose.yml`

3. **Environment Variables** hinzufügen (kritisch!):
   ```
   OPENROUTER_API_KEY=sk-or-v1-...
   UNSPLASH_ACCESS_KEY=...
   PEXELS_API_KEY=...
   SIGHTENGINE_API_USER=...
   SIGHTENGINE_API_SECRET=...
   FLUX_API_KEY=...
   ```

4. **Deploy** klicken

5. **Logs prüfen**:
   - Stack → Container: `npe1-colecture` → Logs
   - Erfolgreiche Meldung: `=== SUCCESS: App imported!`

6. **API testen**:
   ```bash
   curl http://YOUR_SERVER:8080/
   ```

**Wichtige Hinweise:**
- Der Service nutzt Port `8080` und ist über das `cloudflare_net` Netzwerk erreichbar
- Bei Problemen: Stack komplett löschen und neu deployen (Build-Cache!)
- Detaillierte Deployment-Anleitung: [PORTAINER.md](PORTAINER.md)

### Lokale Entwicklung (Docker Compose)

Für lokale Tests mit Docker:

```bash
# 1. .env Datei erstellen
cp .env.example .env
# API-Keys in .env eintragen

# 2. Service starten
docker-compose up -d

# 3. Logs prüfen
docker-compose logs -f

# 4. Service stoppen
docker-compose down
```

**Hinweis**: Für lokale Entwicklung sollte in `docker-compose.yml` das Volume `./src:/app/src` wieder aktiviert werden für Live-Reloading.

### Lokale Entwicklung (Python)

Für Development ohne Docker:

```bash
# 1. Virtual Environment erstellen
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 2. Dependencies installieren
pip install -r requirements.txt

# 3. .env konfigurieren
cp .env.example .env
# API-Keys eintragen

# 4. Server starten
python run_server.py
```

API läuft dann auf: `http://localhost:8080`

## API Endpoints

### Health Check
```bash
GET http://localhost:8080/
```

Response:
```json
{
  "service": "NPE1 Colecture Image Generator",
  "status": "running",
  "version": "1.0.0"
}
```

### Generate Image

**Basis-Request:**
```bash
POST http://localhost:8080/generate-image
Content-Type: application/json

{
  "title": "Lean Production",
  "unsplashSearchTerms": ["manufacturing", "efficiency"],
  "bullets": [
    {"bullet": "Kontinuierliche Prozessoptimierung", "sub": []},
    {"bullet": "Waste Reduction", "sub": []}
  ]
}
```

**Erweitert mit allen Features:**
```bash
POST http://localhost:8080/generate-image
Content-Type: application/json

{
  "title": "Digital Transformation",
  "bullets": [
    {"bullet": "Cloud Migration", "sub": []},
    {"bullet": "AI Integration", "sub": []}
  ],
  "style": ["modern", "minimal", "professional"],
  "image_mode": "ai_only",
  "ai_model": "imagen",
  "colors": {
    "primary": "#0066CC",
    "secondary": "#00CC66"
  }
}
```

**Parameter-Übersicht:**

| Parameter | Typ | Default | Beschreibung |
|-----------|-----|---------|--------------|
| `title` | string | **required** | Folientitel |
| `bullets` | array | optional | Bullet points mit Sub-Items |
| `unsplashSearchTerms` | array | optional | Vordefinierte Keywords (überschreibt Auto-Extraktion) |
| `style` | array | optional | Style-Vorgaben (z.B. `["minimal", "modern", "corporate"]`) |
| `image_mode` | string | `"auto"` | Bildquelle: `"stock_only"`, `"ai_only"`, `"auto"` |
| `ai_model` | string | `"flux"` | KI-Modell: `"flux"` oder `"imagen"` |
| `colors` | object | optional | Farbschema: `{"primary": "...", "secondary": "..."}` |

**Image Modes:**
- `stock_only`: Nur Stock-Fotos, keine KI-Generierung
- `ai_only`: Nur KI-Generierung, keine Stock-Suche
- `auto`: Stock-Fotos bevorzugen, bei Bedarf KI-Generierung (Standard)

Response:
```json
{
  "url": "https://images.unsplash.com/photo-...",
  "source": "stock_unsplash",
  "keywords": "manufacturing, efficiency, factory"
}
```

Mögliche `source` Werte:
- `stock_unsplash` - Gefunden auf Unsplash
- `stock_pexels` - Gefunden auf Pexels
- `generated_flux` - KI-generiert mit FLUX
- `generated_imagen` - KI-generiert mit Google Imagen
- `none` - Keine passenden Bilder gefunden (stock_only Mode)
- `failed` - Generierung fehlgeschlagen

### Generate Image (Simplified GET)

**Für einfache HTTP-Clients ohne JSON-Support:**

```bash
GET /generate-image-simple?title=Digital+Transformation&style=modern,minimal&image_mode=ai_only&ai_model=imagen&primary_color=%230066CC&secondary_color=%2300CC66
```

**Query-Parameter:**

| Parameter | Typ | Default | Beschreibung |
|-----------|-----|---------|--------------|
| `title` | string | **required** | Folientitel (URL-encoded) |
| `style` | string | optional | Komma-getrennte Styles: `modern,minimal,professional` |
| `image_mode` | string | `auto` | Bildquelle: `stock_only`, `ai_only`, `auto` |
| `ai_model` | string | `flux` | KI-Modell: `flux` oder `imagen` |
| `primary_color` | string | optional | Primärfarbe (URL-encoded): `%230066CC` oder `blue` |
| `secondary_color` | string | optional | Sekundärfarbe |
| `keywords` | string | optional | Komma-getrennte Keywords (überschreibt Auto-Extraktion) |

**Beispiele:**

```bash
# Minimales Beispiel
GET /generate-image-simple?title=Lean+Production

# Mit allen Optionen
GET /generate-image-simple?title=Digital+Transformation&style=modern,minimal&image_mode=ai_only&ai_model=flux&primary_color=%230066CC&secondary_color=green&keywords=technology,innovation

# Nur Stock-Fotos
GET /generate-image-simple?title=Teamwork&image_mode=stock_only&keywords=business,collaboration
```

**Browser-freundlich:** Dieser Endpunkt kann direkt im Browser aufgerufen werden!

Response: Identisch zu POST `/generate-image`

### Extract Keywords (Debug)
```bash
POST http://localhost:8080/extract-keywords
Content-Type: application/json

{
  "title": "Digital Transformation",
  "bullets": []
}
```

Response:
```json
{
  "detailed": {
    "skip": false,
    "topics_de": ["Digitalisierung", "Innovation", "Technologie"],
    "english_keywords": ["digital", "technology", "innovation", "cloud", "automation"],
    "style": ["modern", "minimal"],
    "negative_keywords": ["text", "diagram", "screenshot"],
    "constraints": {"orientation": "landscape", "color": null}
  },
  "refined": "digital transformation, technology"
}
```

### Interaktive API-Dokumentation

Swagger UI: `http://localhost:8080/docs`

ReDoc: `http://localhost:8080/redoc`

## Architecture

```
src/
├── config.py           # Configuration management
├── models.py           # Pydantic data models
├── keyword_extractor.py # LLM-based keyword extraction
├── image_search.py     # Stock photo search (Unsplash/Pexels)
├── image_scorer.py     # Quality and safety scoring
├── image_generator.py  # AI image generation (FLUX)
├── orchestrator.py     # Main pipeline orchestration
└── api.py              # FastAPI application
```

## Deployment

### Portainer

Siehe detaillierte Anleitung: [PORTAINER.md](PORTAINER.md)

**Quick Start:**
1. Portainer → Stacks → Add stack
2. Git Repository: `https://github.com/gurkepunktli/npe1-colecture`
3. Environment Variables mit API Keys konfigurieren
4. Deploy

## License

TBD

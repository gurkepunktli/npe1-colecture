# NPE1 Colecture - Image Generator

AI-powered image finder and generator for PowerPoint presentations using LangChain.

This project reimplements an n8n workflow in Python using LangChain to:
- Extract relevant keywords from slide content
- Search stock photo services (Unsplash, Pexels)
- Score images for quality and presentation suitability
- Generate AI images as fallback using FLUX

## Features

- **Intelligent Keyword Extraction**: Uses LLMs to extract presentation-relevant keywords from slide text
- **Multi-Source Image Search**: Searches both Unsplash and Pexels APIs
- **Quality Scoring**: Evaluates images for technical quality and topic relevance
- **Safety Checks**: Filters out inappropriate content
- **AI Fallback**: Generates custom images when stock photos don't match
- **REST API**: FastAPI server for easy integration

## Setup

1. Clone the repository:
```bash
git clone https://github.com/gurkepunktli/npe1-colecture.git
cd npe1-colecture
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Configure environment variables:
```bash
cp .env.example .env
# Edit .env with your API keys
```

## Configuration

Required API keys (add to [.env](.env)):
- `OPENROUTER_API_KEY`: For LLM access (Gemini, Claude)
- `UNSPLASH_ACCESS_KEY`: For Unsplash image search
- `PEXELS_API_KEY`: For Pexels image search
- `SIGHTENGINE_API_USER` & `SIGHTENGINE_API_SECRET`: For image quality/safety checks
- `FLUX_API_KEY`: For AI image generation

Optional:
- `SCORING_SERVICE_URL`: Local service for presentation fit scoring

## Usage

### Option 1: Docker (Empfohlen)

1. Configure environment:
```bash
cp .env.example .env
# Edit .env with your API keys
```

2. Start the service:
```bash
docker-compose up -d
```

3. Check logs:
```bash
docker-compose logs -f
```

4. Stop the service:
```bash
docker-compose down
```

### Option 2: Local Python

1. Create virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

2. Run CLI test:
```bash
python main.py
```

3. Or start API server:
```bash
python run_server.py
```

### API Usage

API is available at `http://localhost:8080`

Swagger docs: `http://localhost:8080/docs`

Example request:
```bash
curl -X POST http://localhost:8080/generate-image \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Lean Production",
    "unsplashSearchTerms": ["manufacturing", "efficiency"],
    "bullets": [{"bullet": "Production optimization", "sub": []}]
  }'
```

Response:
```json
{
  "url": "https://images.unsplash.com/...",
  "source": "stock_unsplash",
  "keywords": "manufacturing, efficiency"
}
```

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

## License

TBD

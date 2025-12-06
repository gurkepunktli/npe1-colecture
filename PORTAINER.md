# Portainer Deployment Guide

## Option 1: Docker Compose Stack (Empfohlen)

### Schritt 1: Stack erstellen

1. Öffne Portainer UI
2. Navigiere zu **Stacks** → **Add stack**
3. Name: `npe1-colecture`
4. Build method: **Git Repository**

### Schritt 2: Repository konfigurieren

**Git Repository:**
```
https://github.com/gurkepunktli/npe1-colecture
```

**Reference:** `refs/heads/main`

**Compose path:** `docker-compose.yml`

### Schritt 3: Environment Variables

**WICHTIG:** Scrolle runter und klicke auf **Environment variables** → **Advanced mode**

Füge folgende Variablen ein (eine pro Zeile, ohne Anführungszeichen):

```
OPENROUTER_API_KEY=sk-or-v1-xxxxx
UNSPLASH_ACCESS_KEY=xxxxx
PEXELS_API_KEY=xxxxx
SIGHTENGINE_API_USER=xxxxx
SIGHTENGINE_API_SECRET=xxxxx
FLUX_API_KEY=xxxxx
SCORING_SERVICE_URL=http://192.168.100.14:8000
MIN_PRESENTATION_SCORE=0.6
MIN_QUALITY_SCORE=0.7
MIN_NUDITY_SAFE_SCORE=0.99
```

**Tipp:** Die Vorlage findest du auch in [.env.portainer](.env.portainer)

### Schritt 4: Deploy

**WICHTIG:** Der Service nutzt das externe Netzwerk `cloudflare_net`.

Das Netzwerk ist bereits im `docker-compose.yml` konfiguriert:
```yaml
networks:
  cloudflare_net:
    external: true
```

Stelle sicher, dass das Netzwerk `cloudflare_net` existiert, sonst:
```bash
docker network create cloudflare_net
```

1. Klicke auf **Deploy the stack**
2. Warte bis der Build abgeschlossen ist
3. Service läuft auf Port **8080** im Netzwerk `cloudflare_net`

---

## Option 2: Container direkt erstellen

### Schritt 1: Image bauen (optional)

Falls du das Image selbst bauen möchtest:

1. **Containers** → **Add container**
2. Name: `npe1-colecture`
3. Image: Wähle **Build**
4. Git Repository: `https://github.com/gurkepunktli/npe1-colecture`
5. Dockerfile path: `Dockerfile`

### Schritt 2: Container konfigurieren

**Image configuration:**
- Name: `npe1-colecture`
- Image: `npe1-colecture:latest` (nach Build) oder baue mit GitHub

**Network ports configuration:**
- Map port `8080` → `8080` (oder anderer Host-Port)

**Network:**
- Network: `cloudflare_net`

**Advanced container settings:**

**Env variables:**
```
OPENROUTER_API_KEY=sk-or-v1-xxxxx
UNSPLASH_ACCESS_KEY=xxxxx
PEXELS_API_KEY=xxxxx
SIGHTENGINE_API_USER=xxxxx
SIGHTENGINE_API_SECRET=xxxxx
FLUX_API_KEY=xxxxx
PYTHONUNBUFFERED=1
```

**Restart policy:** `Unless stopped`

### Schritt 3: Deploy

Klicke auf **Deploy the container**

---

## Option 3: Pre-built Image von Docker Hub (Falls publiziert)

Wenn du ein Image auf Docker Hub publishen möchtest:

```bash
# Lokal bauen und pushen
docker build -t gurkepunktli/npe1-colecture:latest .
docker push gurkepunktli/npe1-colecture:latest
```

Dann in Portainer:
- Image: `gurkepunktli/npe1-colecture:latest`
- Rest wie Option 2

---

## Zugriff testen

Nach dem Deployment:

1. **Health Check:**
   ```bash
   curl http://YOUR_SERVER:8080/
   ```

2. **Swagger UI:**
   ```
   http://YOUR_SERVER:8080/docs
   ```

3. **API Test:**
   ```bash
   curl -X POST http://YOUR_SERVER:8080/generate-image \
     -H "Content-Type: application/json" \
     -d '{
       "title": "Test Slide",
       "unsplashSearchTerms": ["technology", "business"],
       "bullets": [{"bullet": "Test", "sub": []}]
     }'
   ```

---

## Logs anzeigen

In Portainer:
1. **Containers** → `npe1-colecture`
2. **Logs** Tab
3. Oder **Stats** für Resource-Nutzung

---

## Troubleshooting

### Container startet nicht

**Logs prüfen:**
1. Portainer → Containers → npe1-colecture → Logs

**Häufige Fehler:**
- Fehlende API Keys → Environment Variables prüfen
- Port bereits belegt → Port-Mapping ändern
- Build-Fehler → Git Repository URL prüfen

### API antwortet nicht

```bash
# Container Status prüfen
docker ps | grep npe1-colecture

# Logs live anzeigen
docker logs -f npe1-colecture

# In Container einsteigen
docker exec -it npe1-colecture /bin/bash
```

### API Keys aktualisieren

**Mit Stack:**
1. Stacks → npe1-colecture → Editor
2. Environment Variables aktualisieren
3. **Update the stack**

**Mit Container:**
1. Container stoppen
2. Environment Variables bearbeiten
3. Container neu starten

---

## Ressourcen-Limits (Optional)

In Portainer unter **Resources and limits:**

```
Memory limit: 512 MB
Memory reservation: 256 MB
CPU limit: 1.0
```

Anpassen je nach Last und verfügbaren Ressourcen.

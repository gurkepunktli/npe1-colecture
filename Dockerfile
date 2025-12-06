FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source files
COPY src/ /app/src/
COPY main.py run_server.py /app/

# Debug: Check what was copied and test imports
RUN echo "=== Contents of /app ===" && ls -la /app && \
    echo "=== Contents of /app/src ===" && ls -la /app/src && \
    echo "=== Testing Python imports ===" && \
    python -c "import sys; sys.path.insert(0, '/app'); print('Path OK'); import src; print('src OK'); from src import models; print('models OK'); from src import config; print('config OK')" || echo "Import failed - but continuing..."

# Expose port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8080/')" || exit 1

# Run with explicit python path
CMD ["python", "-m", "uvicorn", "src.api:app", "--host", "0.0.0.0", "--port", "8080"]

FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy EVERYTHING (let .dockerignore handle exclusions)
COPY . /app/

# Debug: verify files copied
RUN echo "=== Build time check ===" && \
    ls -la /app && \
    echo "=== src directory ===" && \
    ls -la /app/src || echo "src/ is empty or missing!"

# Expose port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8080/')" || exit 1

# Run using direct app import
CMD ["python", "start.py"]

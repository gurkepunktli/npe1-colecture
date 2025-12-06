FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy root-level Python files
COPY *.py /app/
COPY stack.env .env.example /app/

# Copy src directory explicitly
COPY src/ /app/src/

# Debug: verify files copied
RUN echo "=== Build time check ===" && \
    ls -la /app && \
    echo "=== src directory ===" && \
    ls -la /app/src && \
    echo "=== Checking specific files ===" && \
    test -f /app/src/__init__.py && echo "src/__init__.py: YES" || echo "src/__init__.py: NO" && \
    test -f /app/src/api.py && echo "src/api.py: YES" || echo "src/api.py: NO"

# Expose port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8080/')" || exit 1

# Run using direct app import
CMD ["python", "start.py"]

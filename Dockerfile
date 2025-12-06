FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Debug: Show what we have in build context BEFORE copying
RUN echo "=== Docker build context check (should fail, but shows us the context) ===" || true

# Copy root-level Python files
COPY *.py ./
COPY stack.env .env.example ./

# Debug: Check what got copied so far
RUN echo "=== After copying root files ===" && ls -la /app

# Copy src directory explicitly with trailing slash
COPY src/ ./src/

# Debug: Comprehensive verification
RUN echo "=== After copying src/ ===" && \
    ls -la /app && \
    echo "" && \
    echo "=== Contents of /app/src/ ===" && \
    ls -la /app/src/ && \
    echo "" && \
    echo "=== File count in src/ ===" && \
    find /app/src -type f | wc -l && \
    echo "" && \
    echo "=== All files in src/ ===" && \
    find /app/src -type f

# Expose port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8080/')" || exit 1

# Run using direct app import
CMD ["python", "start.py"]

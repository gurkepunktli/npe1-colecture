FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY *.py ./
COPY stack.env .env.example ./
COPY src/ ./src/

# Verify build (can be removed after successful deployment)
RUN echo "=== Build verification ===" && \
    echo "src/ contents:" && ls -la /app/src/ && \
    echo "" && \
    echo "Total Python files in src/:" && ls -1 /app/src/*.py | wc -l

# Expose port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8080/')" || exit 1

# Run using direct app import
CMD ["python", "start.py"]

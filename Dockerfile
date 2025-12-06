FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ ./src/
COPY main.py run_server.py ./

# Set Python path
ENV PYTHONPATH=/app

# Expose port
EXPOSE 8080

# Health check - give app more time to start
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8080/')" || exit 1

# Run the server
CMD ["python", "run_server.py"]

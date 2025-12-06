"""Startup script for the API server."""
import sys
import os

# Ensure /app is in Python path
sys.path.insert(0, '/app')
os.chdir('/app')

# Now import and run
if __name__ == "__main__":
    import uvicorn
    from src.api import app

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8080
    )
"""Startup script for the API server."""
import sys
import os

# Debug: Show what's in /app
print("=== Current directory:", os.getcwd())
print("=== sys.path:", sys.path)
print("=== /app contents:", os.listdir('/app'))
print("=== /app/src contents:", os.listdir('/app/src') if os.path.exists('/app/src') else "NOT FOUND")

# Ensure /app is in Python path
sys.path.insert(0, '/app')
os.chdir('/app')

# Try import
if __name__ == "__main__":
    try:
        import uvicorn
        from src.api import app

        print("=== SUCCESS: App imported!")
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=8080
        )
    except Exception as e:
        print(f"=== ERROR: {e}")
        import traceback
        traceback.print_exc()
        # Keep container running for debugging
        import time
        time.sleep(3600)
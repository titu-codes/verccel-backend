"""Start the backend server - run with: python start_server.py"""
import os
import sys

# Force SQLite for local dev (set USE_SQLITE=0 to use MySQL from .env)
if os.getenv("USE_SQLITE", "1") != "0":
    os.environ["USE_SQLITE"] = "true"

if __name__ == "__main__":
    print("Loading HRMS backend...", flush=True)
    try:
        from app.main import app
        print("App loaded. Starting server on http://127.0.0.1:8000", flush=True)
    except Exception as e:
        print(f"Failed to load app: {e}", flush=True)
        import traceback
        traceback.print_exc()
        sys.exit(1)

    import uvicorn
    uvicorn.run(
        app,
        host="127.0.0.1",
        port=8000,
        log_level="info"
    )

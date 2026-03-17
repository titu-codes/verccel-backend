import os
import uvicorn

# Use SQLite for local dev when MySQL is unavailable (set USE_SQLITE=0 to use MySQL)
if os.getenv("USE_SQLITE", "1") != "0":
    os.environ["USE_SQLITE"] = "true"

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="127.0.0.1",
        port=8000,
        reload=True
    )
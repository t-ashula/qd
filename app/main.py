import os

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.api.api import api_router
from app.db.database import init_db
from app.vectorstore.qdrant import qdrant_manager

# Create FastAPI app
app = FastAPI(title="QD - Audio Transcription and Search")

# Mount static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Include API router
app.include_router(api_router)


@app.on_event("startup")
async def startup_event():
    """
    Initialize database and Qdrant collections on startup
    """
    # Initialize database
    init_db()

    # Initialize Qdrant collections
    qdrant_manager.init_collections()

    # Create media directory if it doesn't exist
    os.makedirs("media", exist_ok=True)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)

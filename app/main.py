import contextlib
import os
import subprocess

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.api.api import api_router
from app.db.database import init_db
from app.vectorstore.qdrant import qdrant_manager


# Create FastAPI app with lifespan
@contextlib.asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for FastAPI app
    Handles startup and shutdown events
    """
    # --- Startup actions ---
    print("Initializing application...")

    # Initialize database
    init_db()

    # Run Alembic migrations
    subprocess.run(["poetry", "run", "alembic", "upgrade", "head"], check=True)

    # Initialize Qdrant collections
    qdrant_manager.init_collections()

    # Create media directory if it doesn't exist
    os.makedirs("media", exist_ok=True)

    print("Application initialized successfully")

    # Yield control back to FastAPI
    yield

    # --- Shutdown actions ---
    print("Shutting down application...")
    # Add any cleanup code here if needed
    print("Application shutdown complete")


# Create FastAPI app with lifespan
app = FastAPI(title="QD - Audio Transcription and Search", lifespan=lifespan)

# Mount static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Include API router
app.include_router(api_router)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)

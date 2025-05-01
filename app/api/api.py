from fastapi import APIRouter

from app.api import episodes, main, media, upload

# Create API router
api_router = APIRouter()

# Include routers
api_router.include_router(main.router, tags=["main"])
api_router.include_router(episodes.router, prefix="/episodes", tags=["episodes"])
api_router.include_router(media.router, prefix="/media", tags=["media"])
api_router.include_router(upload.router, prefix="/upload", tags=["upload"])

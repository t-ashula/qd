import os
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException, Path
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.services.episode import episode_service
from app.services.storage import storage_service

# Create router
router = APIRouter()


@router.get("/{episode_id}.{ext}")
async def get_media(
    episode_id: str = Path(...), ext: str = Path(...), db: Session = Depends(get_db)
):
    """
    Media file endpoint
    """
    # Get episode data
    episode_data = episode_service.get_episode(episode_id, db)

    # If episode not found, raise 404
    if not episode_data:
        raise HTTPException(status_code=404, detail="Episode not found")

    # Check if file exists
    if not storage_service.file_exists(episode_id, ext):
        raise HTTPException(status_code=404, detail="Media file not found")

    # Get file path
    file_path = storage_service.get_file_path(episode_id, ext)

    # Return file
    return FileResponse(
        path=file_path,
        media_type=episode_data["media_type"],
        filename=f"{episode_data['name']}",
    )

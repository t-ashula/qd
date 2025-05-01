from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException, Path, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.services.episode import episode_service

# Create router
router = APIRouter()

# Templates
templates = Jinja2Templates(directory="app/templates")


@router.get("/{episode_id}", response_class=HTMLResponse)
async def get_episode(
    request: Request, episode_id: str = Path(...), db: Session = Depends(get_db)
):
    """
    Episode details page
    """
    # Get episode data
    episode_data = episode_service.get_episode_with_segments(episode_id, db)

    # If episode not found, raise 404
    if not episode_data:
        raise HTTPException(status_code=404, detail="Episode not found")

    return templates.TemplateResponse(
        "episode.html", {"request": request, "episode": episode_data}
    )

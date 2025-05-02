from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Path, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.services.episode import episode_service

# Create router
router = APIRouter()

# Templates
templates = Jinja2Templates(directory="app/templates")


@router.get("", response_class=HTMLResponse)
async def list_episodes(
    request: Request,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """
    List episodes page with pagination
    """
    # Get episodes data with pagination
    episodes_data = episode_service.get_episodes_list(page, per_page, db)

    return templates.TemplateResponse(
        "episodes.html", {"request": request, "data": episodes_data}
    )


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

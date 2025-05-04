from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Path, Query, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.models import Episode, TranscribeHistory
from app.services.episode import episode_service
from app.services.storage import storage_service
from app.transcriber.transcriber import AVAILABLE_MODELS, transcriber_service
from app.vectorstore.qdrant import qdrant_manager

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


# Define request model for transcription
class TranscribeRequest(BaseModel):
    model_name: str


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

    # Get available models
    available_models = transcriber_service.get_available_models()

    # Get used models for this episode
    used_models = []
    all_models_used = False
    current_history_id = None

    if "transcription_histories" in episode_data:
        used_models = [
            str(h["model_name"]) for h in episode_data["transcription_histories"]
        ]
        all_models_used = len(used_models) >= len(available_models)
        if episode_data["transcription_histories"]:
            current_history_id = episode_data["transcription_histories"][0]["id"]

    return templates.TemplateResponse(
        "episode.html",
        {
            "request": request,
            "episode": episode_data,
            "available_models": available_models,
            "used_models": used_models,
            "all_models_used": all_models_used,
            "current_history_id": current_history_id,
        },
    )


@router.get("/{episode_id}/segments")
async def get_episode_segments(
    episode_id: str = Path(...),
    history_id: int = Query(...),
    db: Session = Depends(get_db),
):
    """
    Get episode segments for a specific transcription history
    """
    # Check if episode exists
    episode = db.query(Episode).filter(Episode.id == episode_id).first()
    if not episode:
        raise HTTPException(status_code=404, detail="Episode not found")

    # Check if history exists
    history = (
        db.query(TranscribeHistory)
        .filter(
            TranscribeHistory.id == history_id,
            TranscribeHistory.episode_id == episode_id,
        )
        .first()
    )
    if not history:
        raise HTTPException(status_code=404, detail="Transcription history not found")

    # Get segments
    segments = episode_service.get_episode_segments(episode_id, db, history_id)

    return {"segments": segments}


@router.post("/{episode_id}/transcribe")
async def transcribe_episode(
    request: TranscribeRequest,
    episode_id: str = Path(...),
    db: Session = Depends(get_db),
):
    """
    Transcribe episode with a different model
    """
    # Check if episode exists
    episode = db.query(Episode).filter(Episode.id == episode_id).first()
    if not episode:
        raise HTTPException(status_code=404, detail="Episode not found")

    # Check if model is valid
    model_name = request.model_name
    if model_name not in AVAILABLE_MODELS:
        raise HTTPException(status_code=400, detail="Invalid model name")

    # Check if episode has already been transcribed with this model
    existing_history = (
        db.query(TranscribeHistory)
        .filter(
            TranscribeHistory.episode_id == episode_id,
            TranscribeHistory.model_name == model_name,
        )
        .first()
    )
    if existing_history:
        raise HTTPException(
            status_code=400, detail="Episode already transcribed with this model"
        )

    # Get file path
    file_path = storage_service.get_file_path(episode_id, str(episode.ext))

    # Transcribe audio
    transcription = transcriber_service.transcribe(file_path, model_name)

    # Create transcribe history record
    transcribe_history = TranscribeHistory(
        episode_id=episode_id,
        model_name=model_name,
    )
    db.add(transcribe_history)
    db.flush()  # Get ID without committing

    # Process transcription chunks
    from app.services.upload import upload_service

    upload_service._process_transcription(
        transcription, episode_id, int(transcribe_history.id), db
    )

    return {"success": True, "history_id": transcribe_history.id}


@router.delete("/{episode_id}")
async def delete_episode(episode_id: str = Path(...), db: Session = Depends(get_db)):
    """
    Delete episode and all related data
    """
    # Get episode data
    episode_data = episode_service.get_episode(episode_id, db)

    # If episode not found, raise 404
    if not episode_data:
        raise HTTPException(status_code=404, detail="Episode not found")

    # Delete media file
    storage_service.delete_file(episode_id, episode_data["ext"])

    # Delete vector embeddings
    qdrant_manager.delete_points_by_episode_id(episode_id)

    # Delete episode from database
    episode_service.delete_episode(episode_id, db)

    # Redirect to episodes list
    return RedirectResponse(url="/episodes", status_code=303)

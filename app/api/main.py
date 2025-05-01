from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.services.search import search_service

# Create router
router = APIRouter()

# Templates
templates = Jinja2Templates(directory="app/templates")


@router.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """
    Home page
    """
    return templates.TemplateResponse("index.html", {"request": request})


@router.get("/search", response_class=HTMLResponse)
async def search(
    request: Request, q: Optional[str] = Query(None), db: Session = Depends(get_db)
):
    """
    Search page
    """
    # If no query, redirect to home
    if not q:
        return RedirectResponse(url="/")

    # Search for query
    results = search_service.search(q)

    return templates.TemplateResponse(
        "search.html", {"request": request, "query": q, "results": results}
    )

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.services.upload import upload_service

# Create router
router = APIRouter()

# Templates
templates = Jinja2Templates(directory="app/templates")


@router.get("/", response_class=HTMLResponse)
async def upload_form(request: Request):
    """
    Upload form page
    """
    return templates.TemplateResponse("upload.html", {"request": request})


@router.post("/", response_class=RedirectResponse)
async def upload_file(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """
    Upload file endpoint
    """
    try:
        # Process upload
        episode_id = upload_service.process_upload(file.file, f"{file.filename}", db)

        # Redirect to episode page
        return RedirectResponse(url=f"/episodes/{episode_id}", status_code=303)

    except ValueError as e:
        # If media type not supported, raise 400
        raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:
        # If any other error, raise 500
        print(e.__traceback__)
        raise HTTPException(status_code=500, detail={"error": str(e)})

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.services.upload import upload_service
from app.transcriber.transcriber import DEFAULT_MODEL, transcriber_service

# Create router
router = APIRouter()

# Templates
templates = Jinja2Templates(directory="app/templates")


@router.get("/", response_class=HTMLResponse)
async def upload_form(request: Request):
    """
    Upload form page
    """
    # Get available models for template
    available_models = transcriber_service.get_available_models()
    return templates.TemplateResponse(
        "upload.html",
        {
            "request": request,
            "available_models": available_models,
            "default_model": DEFAULT_MODEL,
        },
    )


@router.post("/", response_class=RedirectResponse)
async def upload_file(
    file: UploadFile = File(...),
    model_name: str = Form(DEFAULT_MODEL),
    db: Session = Depends(get_db),
):
    """
    Upload file endpoint

    Args:
        file: Uploaded file
        model_name: Name of the transcription model to use
        db: Database session
    """
    episode_id = None
    extension = None

    try:
        # Process upload with specified model
        episode_id = upload_service.process_upload(
            file.file, f"{file.filename}", db, model_name
        )

        # Redirect to episode page
        return RedirectResponse(url=f"/episodes/{episode_id}", status_code=303)

    except ValueError as e:
        # If media type not supported, raise 400
        raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:
        # If any other error, clean up resources and raise 500
        print(f"Error during upload: {str(e)}")
        print(e.__traceback__)

        # Clean up resources if episode_id was created
        if episode_id:
            # Try to determine file extension from filename
            if file.filename is not None and "." in file.filename:
                extension = file.filename.split(".")[-1].lower()
            else:
                # Default to mp3 if no extension found
                extension = "mp3"

            # Clean up resources
            upload_service.cleanup_resources(episode_id, extension, db)

        # Raise HTTP exception
        raise HTTPException(status_code=500, detail={"error": str(e)})

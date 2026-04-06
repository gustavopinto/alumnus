import logging

from fastapi import APIRouter, Depends, UploadFile, File
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_current_user
from ..services import upload_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/upload", tags=["upload"])


@router.post("/photo")
async def upload_photo(file: UploadFile = File(...), db: Session = Depends(get_db)):
    file_id, thumb_file_id = await upload_service.save_researcher_photo(file, db)
    return {"file_id": file_id, "thumb_file_id": thumb_file_id}


@router.post("/image")
async def upload_image(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Upload de imagem para embed em conteúdo rich text."""
    url, _ = await upload_service.save_upload(file, db)
    return {"url": url}

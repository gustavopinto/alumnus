import logging

from fastapi import APIRouter, Depends, UploadFile, File
from sqlalchemy.orm import Session

from ..database import get_db
from ..services import upload_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/upload", tags=["upload"])


@router.post("/photo")
async def upload_photo(file: UploadFile = File(...), db: Session = Depends(get_db)):
    url, thumb_url = await upload_service.save_researcher_photo(file, db)
    return {"url": url, "thumb_url": thumb_url}

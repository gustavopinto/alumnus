import logging

from fastapi import APIRouter, Depends, UploadFile, File
from sqlalchemy.orm import Session

from ..database import get_db
from ..services import upload_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/upload", tags=["upload"])


@router.post("/photo")
async def upload_photo(file: UploadFile = File(...), db: Session = Depends(get_db)):
    file_id, thumb_file_id = await upload_service.save_researcher_photo(file, db)
    return {"file_id": file_id, "thumb_file_id": thumb_file_id}

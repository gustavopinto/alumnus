import logging

from fastapi import APIRouter, Depends, UploadFile, File
from sqlalchemy.orm import Session

from ..database import get_db
from ..fileutils import save_upload

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/upload", tags=["upload"])


@router.post("/photo")
async def upload_photo(file: UploadFile = File(...), db: Session = Depends(get_db)):
    url, _ = await save_upload(file, db)
    logger.info("Photo uploaded: %s", url)
    return {"url": url}

import logging

from fastapi import APIRouter, UploadFile, File

from ..fileutils import save_upload

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/upload", tags=["upload"])


@router.post("/photo")
async def upload_photo(file: UploadFile = File(...)):
    url, _ = await save_upload(file)
    logger.info("Photo uploaded: %s", url)
    return {"url": url}

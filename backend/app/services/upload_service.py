import logging

from fastapi import UploadFile
from sqlalchemy.orm import Session

from ..fileutils import save_upload as persist_upload

logger = logging.getLogger(__name__)


async def save_upload(file: UploadFile, db: Session) -> tuple[str, str]:
    """Validate, store file; returns (url, original_filename)."""
    url, name = await persist_upload(file, db)
    logger.info("Photo uploaded: %s", url)
    return url, name

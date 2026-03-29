import asyncio
import logging
from pathlib import Path

from fastapi import HTTPException, UploadFile
from sqlalchemy.orm import Session

from ..fileutils import (
    MAX_BYTES,
    IMAGE_EXTS,
    build_portrait_and_thumb_jpeg,
    save_upload as persist_upload,
    _store_bytes,
)

logger = logging.getLogger(__name__)


async def save_upload(file: UploadFile, db: Session) -> tuple[str, str]:
    """Validate, store file; returns (url, original_filename)."""
    url, name = await persist_upload(file, db)
    logger.info("Photo uploaded: %s", url)
    return url, name


async def save_researcher_photo(file: UploadFile, db: Session) -> tuple[int, int]:
    """
    Imagem de perfil: gera retrato 3:4 + miniatura; retorna (file_id_principal, file_id_miniatura).
    """
    content = await file.read()
    if len(content) > MAX_BYTES:
        raise HTTPException(status_code=413, detail="Arquivo maior que 5 MB.")

    ext = Path(file.filename).suffix.lower() if file.filename else ""
    if ext not in IMAGE_EXTS:
        raise HTTPException(
            status_code=415,
            detail="Apenas imagens (JPG, PNG, GIF, WebP).",
        )

    main_b, thumb_b = await asyncio.to_thread(build_portrait_and_thumb_jpeg, content)
    file_id = _store_bytes(db, main_b, "image/jpeg", file.filename or "photo.jpg")
    thumb_file_id = _store_bytes(db, thumb_b, "image/jpeg", "thumb.jpg")
    logger.info("Researcher photo stored main id=%s thumb id=%s", file_id, thumb_file_id)
    return file_id, thumb_file_id

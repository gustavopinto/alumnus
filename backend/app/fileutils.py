import io
import asyncio
import logging
from pathlib import Path

from fastapi import HTTPException, UploadFile
from PIL import Image
from sqlalchemy.orm import Session

from .models import FileUpload

logger = logging.getLogger(__name__)

MAX_BYTES = 5 * 1024 * 1024  # 5 MB
ALLOWED_EXTS = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".pdf"}
IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
IMAGE_MAX_DIM = 1024
IMAGE_QUALITY = 60


def _compress_image(content: bytes) -> bytes:
    img = Image.open(io.BytesIO(content))
    if img.mode not in ("RGB", "L"):
        img = img.convert("RGB")
    img.thumbnail((IMAGE_MAX_DIM, IMAGE_MAX_DIM), Image.LANCZOS)
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=IMAGE_QUALITY, optimize=True)
    return buf.getvalue()


async def save_upload(file: UploadFile, db: Session) -> tuple[str, str]:
    """
    Validate, compress if image, store in DB.
    Returns (url, original_filename).
    """
    content = await file.read()

    if len(content) > MAX_BYTES:
        raise HTTPException(status_code=413, detail="Arquivo maior que 5 MB.")

    ext = Path(file.filename).suffix.lower() if file.filename else ""

    if ext not in ALLOWED_EXTS:
        raise HTTPException(
            status_code=415,
            detail="Apenas imagens (JPG, PNG, GIF, WebP) ou PDF são permitidos.",
        )

    if ext in IMAGE_EXTS:
        content = await asyncio.to_thread(_compress_image, content)
        mime_type = "image/jpeg"
    else:
        mime_type = "application/pdf"

    record = FileUpload(
        data=content,
        mime_type=mime_type,
        original_name=file.filename or "file",
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    logger.info("Stored file id=%s (%d bytes)", record.id, len(content))
    return f"/api/files/{record.id}", record.original_name

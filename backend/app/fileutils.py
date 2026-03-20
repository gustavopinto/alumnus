import io
import uuid
import asyncio
import logging
from pathlib import Path

from fastapi import HTTPException, UploadFile
from PIL import Image

logger = logging.getLogger(__name__)

UPLOAD_DIR = Path("/app/uploads")
MAX_BYTES = 5 * 1024 * 1024  # 5 MB
ALLOWED_EXTS = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".pdf"}
IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
IMAGE_MAX_DIM = 1024   # px
IMAGE_QUALITY = 60     # JPEG quality


def _compress_image(content: bytes) -> tuple[bytes, str]:
    """Resize and compress image, return (bytes, .jpg)."""
    img = Image.open(io.BytesIO(content))
    if img.mode not in ("RGB", "L"):
        img = img.convert("RGB")
    img.thumbnail((IMAGE_MAX_DIM, IMAGE_MAX_DIM), Image.LANCZOS)
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=IMAGE_QUALITY, optimize=True)
    return buf.getvalue(), ".jpg"


def _save_file(content: bytes, ext: str) -> str:
    filename = f"{uuid.uuid4().hex}{ext}"
    (UPLOAD_DIR / filename).write_bytes(content)
    logger.info("Saved file: %s (%d bytes)", filename, len(content))
    return filename


async def save_upload(file: UploadFile) -> tuple[str, str]:
    """
    Validate size, compress if image, save to disk.
    Returns (url, original_filename).
    """
    content = await file.read()

    if len(content) > MAX_BYTES:
        raise HTTPException(status_code=413, detail="Arquivo maior que 5 MB.")

    ext = Path(file.filename).suffix.lower() if file.filename else ""

    if ext not in ALLOWED_EXTS:
        raise HTTPException(status_code=415, detail="Apenas imagens (JPG, PNG, GIF, WebP) ou PDF são permitidos.")

    if ext in IMAGE_EXTS:
        content, ext = await asyncio.to_thread(_compress_image, content)

    filename = await asyncio.to_thread(_save_file, content, ext)
    return f"/uploads/{filename}", file.filename or filename

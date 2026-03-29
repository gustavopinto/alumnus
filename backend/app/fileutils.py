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

# Retrato 3×4 (largura:altura) + miniatura para deadlines
PORTRAIT_MAX_HEIGHT = 640
THUMB_PIXELS = 64
PORTRAIT_JPEG_QUALITY = 82
THUMB_JPEG_QUALITY = 78


def _store_bytes(db: Session, content: bytes, mime_type: str, original_name: str) -> int:
    record = FileUpload(
        data=content,
        mime_type=mime_type,
        original_name=original_name,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record.id


def build_portrait_and_thumb_jpeg(content: bytes) -> tuple[bytes, bytes]:
    """
    Gera JPEG retrato 3:4 (tipo foto documento) e uma miniatura quadrada reduzida.
    """
    img = Image.open(io.BytesIO(content))
    if getattr(img, "n_frames", 1) > 1:
        img.seek(0)
    if img.mode == "P":
        img = img.convert("RGBA")
    if img.mode == "RGBA":
        bg = Image.new("RGB", img.size, (255, 255, 255))
        bg.paste(img, mask=img.split()[3])
        img = bg
    elif img.mode != "RGB":
        img = img.convert("RGB")

    w, h = img.size
    target_ratio = 3 / 4  # largura / altura
    cur_ratio = w / h if h else 1.0
    if cur_ratio > target_ratio:
        new_w = int(h * target_ratio)
        left = (w - new_w) // 2
        img = img.crop((left, 0, left + new_w, h))
    else:
        new_h = int(w / target_ratio)
        top = (h - new_h) // 2
        img = img.crop((0, top, w, top + new_h))

    cropped = img.copy()
    nw, nh = cropped.size
    if nh > PORTRAIT_MAX_HEIGHT:
        scale = PORTRAIT_MAX_HEIGHT / nh
        cropped = cropped.resize((max(1, int(nw * scale)), PORTRAIT_MAX_HEIGHT), Image.LANCZOS)

    buf = io.BytesIO()
    cropped.save(buf, format="JPEG", quality=PORTRAIT_JPEG_QUALITY, optimize=True)
    main_bytes = buf.getvalue()

    tw, th = img.size
    side = min(tw, th)
    left = (tw - side) // 2
    top = (th - side) // 2
    sq = img.crop((left, top, left + side, top + side))
    sq = sq.resize((THUMB_PIXELS, THUMB_PIXELS), Image.LANCZOS)
    buf2 = io.BytesIO()
    sq.save(buf2, format="JPEG", quality=THUMB_JPEG_QUALITY, optimize=True)
    thumb_bytes = buf2.getvalue()

    return main_bytes, thumb_bytes


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

    fid = _store_bytes(db, content, mime_type, file.filename or "file")
    url = f"/api/files/{fid}"
    logger.info("Stored file id=%s (%d bytes)", fid, len(content))
    return url, file.filename or "file"

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import FileUpload

router = APIRouter(prefix="/files", tags=["files"])


@router.get("/{file_id}")
def serve_file(file_id: int, db: Session = Depends(get_db)):
    record = db.query(FileUpload).get(file_id)
    if not record:
        raise HTTPException(status_code=404, detail="File not found")
    return Response(
        content=record.data,
        media_type=record.mime_type,
        headers={"Content-Disposition": f'inline; filename="{record.original_name}"'},
    )

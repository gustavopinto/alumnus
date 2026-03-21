import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import User
from ..schemas import NoteOut
from ..deps import get_optional_user
from ..services import note_service, upload_service

logger = logging.getLogger(__name__)
router = APIRouter(tags=["notes"])


@router.get("/researchers/{researcher_id}/notes", response_model=list[NoteOut])
def list_notes(researcher_id: int, db: Session = Depends(get_db)):
    notes = note_service.list_by_researcher(db, researcher_id)
    return [NoteOut.from_orm_with_creator(n) for n in notes]


@router.post("/researchers/{researcher_id}/notes", response_model=NoteOut, status_code=201)
async def create_note(
    researcher_id: int,
    text: str = Form(...),
    file: UploadFile | None = File(None),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user),
):
    file_url = None
    file_name = None
    if file and file.filename:
        file_url, file_name = await upload_service.save_upload(file, db)

    note = note_service.create(
        db,
        researcher_id,
        text,
        file_url,
        file_name,
        current_user.id if current_user else None,
    )
    return NoteOut.from_orm_with_creator(note)


@router.delete("/notes/{note_id}", status_code=204)
def delete_note(note_id: int, db: Session = Depends(get_db)):
    note = note_service.get_by_id(db, note_id)
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    note_service.delete(db, note)

import logging

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Note
from ..schemas import NoteOut
from ..fileutils import save_upload

logger = logging.getLogger(__name__)
router = APIRouter(tags=["notes"])


@router.get("/students/{student_id}/notes", response_model=list[NoteOut])
def list_notes(student_id: int, db: Session = Depends(get_db)):
    return db.query(Note).filter(Note.student_id == student_id).order_by(Note.created_at.desc()).all()


@router.post("/students/{student_id}/notes", response_model=NoteOut, status_code=201)
async def create_note(
    student_id: int,
    text: str = Form(...),
    file: UploadFile | None = File(None),
    db: Session = Depends(get_db),
):
    file_url = None
    file_name = None
    if file and file.filename:
        file_url, file_name = await save_upload(file, db)

    note = Note(student_id=student_id, text=text, file_url=file_url, file_name=file_name)
    db.add(note)
    db.commit()
    db.refresh(note)
    logger.info("Note created for student %s", student_id)
    return note


@router.delete("/notes/{note_id}", status_code=204)
def delete_note(note_id: int, db: Session = Depends(get_db)):
    note = db.query(Note).get(note_id)
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    db.delete(note)
    db.commit()
    logger.info("Note deleted: id=%s", note_id)

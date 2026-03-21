import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Note, User
from ..schemas import NoteOut
from ..fileutils import save_upload
from ..deps import decode_token

logger = logging.getLogger(__name__)
router = APIRouter(tags=["notes"])
bearer = HTTPBearer(auto_error=False)


def _get_optional_user(
    creds: Optional[HTTPAuthorizationCredentials] = Depends(bearer),
    db: Session = Depends(get_db),
) -> Optional[User]:
    if not creds:
        return None
    try:
        payload = decode_token(creds.credentials)
        user_id = payload.get("sub")
        return db.query(User).get(int(user_id)) if user_id else None
    except Exception:
        return None


@router.get("/researchers/{researcher_id}/notes", response_model=list[NoteOut])
def list_notes(researcher_id: int, db: Session = Depends(get_db)):
    notes = db.query(Note).filter(Note.researcher_id == researcher_id).order_by(Note.created_at.desc()).all()
    return [NoteOut.from_orm_with_creator(n) for n in notes]


@router.post("/researchers/{researcher_id}/notes", response_model=NoteOut, status_code=201)
async def create_note(
    researcher_id: int,
    text: str = Form(...),
    file: UploadFile | None = File(None),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(_get_optional_user),
):
    file_url = None
    file_name = None
    if file and file.filename:
        file_url, file_name = await save_upload(file, db)

    note = Note(
        researcher_id=researcher_id,
        text=text,
        file_url=file_url,
        file_name=file_name,
        created_by_id=current_user.id if current_user else None,
    )
    db.add(note)
    db.commit()
    db.refresh(note)
    logger.info("Note created for researcher %s", researcher_id)
    return NoteOut.from_orm_with_creator(note)


@router.delete("/notes/{note_id}", status_code=204)
def delete_note(note_id: int, db: Session = Depends(get_db)):
    note = db.query(Note).get(note_id)
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    db.delete(note)
    db.commit()
    logger.info("Note deleted: id=%s", note_id)

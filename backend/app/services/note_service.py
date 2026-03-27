import logging
from typing import Optional

from sqlalchemy.orm import Session

from ..models import Note

logger = logging.getLogger(__name__)


def list_by_user(db: Session, user_id: int, institution_id: int | None = None) -> list[Note]:
    q = db.query(Note).filter(Note.user_id == user_id)
    if institution_id is not None:
        q = q.filter(Note.institution_id == institution_id)
    return q.order_by(Note.created_at.desc()).all()


def create(
    db: Session,
    user_id: int,
    text: str,
    file_url: Optional[str],
    file_name: Optional[str],
    created_by_id: Optional[int],
    institution_id: Optional[int] = None,
) -> Note:
    note = Note(
        user_id=user_id,
        institution_id=institution_id,
        text=text,
        file_url=file_url,
        file_name=file_name,
        created_by_id=created_by_id,
    )
    db.add(note)
    db.commit()
    db.refresh(note)
    logger.info("Note created for user %s", user_id)
    return note


def get_by_id(db: Session, note_id: int) -> Note | None:
    return db.query(Note).get(note_id)


def delete(db: Session, note: Note) -> None:
    db.delete(note)
    db.commit()
    logger.info("Note deleted: id=%s", note.id)

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import User
from ..schemas import (
    ManualEntryCreate,
    ManualEntryOut,
    ManualCommentCreate,
    ManualCommentOut,
)
from ..deps import get_current_user
from ..services import manual_service

router = APIRouter(prefix="/manual", tags=["manual"])


@router.get("/", response_model=list[ManualEntryOut])
def list_entries(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    entries = manual_service.list_entries_ordered(db)
    return [ManualEntryOut.from_orm_with_context(e, current_user.id) for e in entries]


@router.post("/", response_model=ManualEntryOut)
def create_entry(
    data: ManualEntryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    entry = manual_service.create_entry(db, data, current_user.id)
    return ManualEntryOut.from_orm_with_context(entry, current_user.id)


@router.delete("/{entry_id}")
def delete_entry(
    entry_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    entry = manual_service.get_entry(db, entry_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")
    if entry.author_id is None or entry.author_id != current_user.id:
        raise HTTPException(status_code=403, detail="Só quem criou a entrada pode removê-la")
    manual_service.delete_entry(db, entry)
    return {"status": "ok"}


@router.post("/{entry_id}/vote")
def toggle_vote(
    entry_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    entry = manual_service.get_entry(db, entry_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")
    voted, vote_count = manual_service.toggle_vote(db, entry, current_user.id)
    return {"voted": voted, "vote_count": vote_count}


@router.post("/{entry_id}/comments", response_model=ManualCommentOut)
def add_comment(
    entry_id: int,
    data: ManualCommentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    entry = manual_service.get_entry(db, entry_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")
    comment = manual_service.add_comment(db, entry_id, data.text, current_user.id)
    return ManualCommentOut.from_orm_with_author(comment)


@router.delete("/comments/{comment_id}")
def delete_comment(
    comment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    comment = manual_service.get_comment(db, comment_id)
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    if comment.author_id is None or comment.author_id != current_user.id:
        raise HTTPException(status_code=403, detail="Só quem escreveu o comentário pode removê-lo")
    manual_service.delete_comment(db, comment)
    return {"status": "ok"}

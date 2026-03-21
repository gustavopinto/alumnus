import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import ManualEntry, ManualVote, ManualComment, User
from ..schemas import ManualEntryCreate, ManualEntryOut, ManualCommentCreate, ManualCommentOut
from ..deps import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/manual", tags=["manual"])


def _ordered_entries(db: Session):
    entries = db.query(ManualEntry).all()
    return sorted(entries, key=lambda e: (-len(e.votes), e.created_at))


@router.get("/", response_model=list[ManualEntryOut])
def list_entries(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    entries = _ordered_entries(db)
    return [ManualEntryOut.from_orm_with_context(e, current_user.id) for e in entries]


@router.post("/", response_model=ManualEntryOut)
def create_entry(data: ManualEntryCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.role != "professor":
        raise HTTPException(status_code=403, detail="Only professors can add manual entries")
    entry = ManualEntry(
        question=data.question,
        answer=data.answer,
        position=data.position or 0,
        author_id=current_user.id,
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return ManualEntryOut.from_orm_with_context(entry, current_user.id)


@router.delete("/{entry_id}")
def delete_entry(entry_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    entry = db.query(ManualEntry).filter(ManualEntry.id == entry_id).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")
    if current_user.role != "professor":
        raise HTTPException(status_code=403, detail="Only professors can delete entries")
    db.delete(entry)
    db.commit()
    return {"status": "ok"}


@router.post("/{entry_id}/vote")
def toggle_vote(entry_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    entry = db.query(ManualEntry).filter(ManualEntry.id == entry_id).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")
    existing = db.query(ManualVote).filter(
        ManualVote.entry_id == entry_id,
        ManualVote.user_id == current_user.id,
    ).first()
    if existing:
        db.delete(existing)
        voted = False
    else:
        db.add(ManualVote(entry_id=entry_id, user_id=current_user.id))
        voted = True
    db.commit()
    db.refresh(entry)
    return {"voted": voted, "vote_count": len(entry.votes)}


@router.post("/{entry_id}/comments", response_model=ManualCommentOut)
def add_comment(entry_id: int, data: ManualCommentCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    entry = db.query(ManualEntry).filter(ManualEntry.id == entry_id).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")
    comment = ManualComment(entry_id=entry_id, text=data.text, author_id=current_user.id)
    db.add(comment)
    db.commit()
    db.refresh(comment)
    return ManualCommentOut.from_orm_with_author(comment)


@router.delete("/comments/{comment_id}")
def delete_comment(comment_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    comment = db.query(ManualComment).filter(ManualComment.id == comment_id).first()
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    if current_user.role != "professor" and comment.author_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not allowed")
    db.delete(comment)
    db.commit()
    return {"status": "ok"}

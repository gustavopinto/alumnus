from sqlalchemy.orm import Session, joinedload

from ..models import ManualComment, ManualEntry, ManualVote
from ..schemas import ManualEntryCreate


def list_entries_ordered(db: Session) -> list[ManualEntry]:
    entries = (
        db.query(ManualEntry)
        .options(
            joinedload(ManualEntry.author),
            joinedload(ManualEntry.votes),
            joinedload(ManualEntry.comments).joinedload(ManualComment.author),
        )
        .all()
    )
    return sorted(entries, key=lambda e: (-len(e.votes), e.created_at))


def get_entry(db: Session, entry_id: int) -> ManualEntry | None:
    return db.query(ManualEntry).filter(ManualEntry.id == entry_id).first()


def create_entry(db: Session, data: ManualEntryCreate, author_id: int) -> ManualEntry:
    entry = ManualEntry(
        question=data.question,
        answer=data.answer,
        position=data.position or 0,
        author_id=author_id,
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


def delete_entry(db: Session, entry: ManualEntry) -> None:
    db.delete(entry)
    db.commit()


def toggle_vote(db: Session, entry: ManualEntry, user_id: int) -> tuple[bool, int]:
    existing = (
        db.query(ManualVote)
        .filter(
            ManualVote.entry_id == entry.id,
            ManualVote.user_id == user_id,
        )
        .first()
    )
    if existing:
        db.delete(existing)
        voted = False
    else:
        db.add(ManualVote(entry_id=entry.id, user_id=user_id))
        voted = True
    db.commit()
    db.refresh(entry)
    return voted, len(entry.votes)


def add_comment(
    db: Session, entry_id: int, text: str, author_id: int
) -> ManualComment:
    comment = ManualComment(entry_id=entry_id, text=text, author_id=author_id)
    db.add(comment)
    db.commit()
    db.refresh(comment)
    return comment


def get_comment(db: Session, comment_id: int) -> ManualComment | None:
    return db.query(ManualComment).filter(ManualComment.id == comment_id).first()


def delete_comment(db: Session, comment: ManualComment) -> None:
    db.delete(comment)
    db.commit()

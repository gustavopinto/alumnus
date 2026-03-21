import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Reminder, User
from ..schemas import ReminderCreate, ReminderUpdate, ReminderOut
from ..deps import decode_token

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/reminders", tags=["reminders"])
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


@router.get("/", response_model=list[ReminderOut])
def list_reminders(db: Session = Depends(get_db)):
    return db.query(Reminder).order_by(Reminder.done, Reminder.due_date.asc().nullslast(), Reminder.created_at.desc()).all()


@router.post("/", response_model=ReminderOut, status_code=201)
def create_reminder(
    data: ReminderCreate,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(_get_optional_user),
):
    reminder = Reminder(
        text=data.text,
        due_date=data.due_date or None,
        created_by_id=current_user.id if current_user else None,
    )
    db.add(reminder)
    db.commit()
    db.refresh(reminder)
    logger.info("Reminder created: id=%s", reminder.id)
    return reminder


@router.put("/{reminder_id}", response_model=ReminderOut)
def update_reminder(reminder_id: int, data: ReminderUpdate, db: Session = Depends(get_db)):
    reminder = db.query(Reminder).get(reminder_id)
    if not reminder:
        raise HTTPException(status_code=404, detail="Reminder not found")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(reminder, key, value)
    db.commit()
    db.refresh(reminder)
    return reminder


@router.delete("/{reminder_id}", status_code=204)
def delete_reminder(reminder_id: int, db: Session = Depends(get_db)):
    reminder = db.query(Reminder).get(reminder_id)
    if not reminder:
        raise HTTPException(status_code=404, detail="Reminder not found")
    db.delete(reminder)
    db.commit()
    logger.info("Reminder deleted: id=%s", reminder_id)

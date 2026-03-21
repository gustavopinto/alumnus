import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import User
from ..schemas import ReminderCreate, ReminderUpdate, ReminderOut
from ..deps import get_optional_user
from ..services import reminder_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/reminders", tags=["reminders"])


@router.get("/", response_model=list[ReminderOut])
def list_reminders(db: Session = Depends(get_db)):
    return reminder_service.list_ordered(db)


@router.post("/", response_model=ReminderOut, status_code=201)
def create_reminder(
    data: ReminderCreate,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user),
):
    return reminder_service.create(
        db,
        data,
        current_user.id if current_user else None,
    )


@router.put("/{reminder_id}", response_model=ReminderOut)
def update_reminder(reminder_id: int, data: ReminderUpdate, db: Session = Depends(get_db)):
    reminder = reminder_service.get_by_id(db, reminder_id)
    if not reminder:
        raise HTTPException(status_code=404, detail="Reminder not found")
    return reminder_service.update(db, reminder, data)


@router.delete("/{reminder_id}", status_code=204)
def delete_reminder(reminder_id: int, db: Session = Depends(get_db)):
    reminder = reminder_service.get_by_id(db, reminder_id)
    if not reminder:
        raise HTTPException(status_code=404, detail="Reminder not found")
    reminder_service.delete(db, reminder)

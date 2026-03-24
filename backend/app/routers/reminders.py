import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import User
from ..schemas import ReminderCreate, ReminderUpdate, ReminderOut
from ..deps import get_optional_user, get_current_user
from ..services import reminder_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/reminders", tags=["reminders"])


@router.get("/", response_model=list[ReminderOut])
def list_reminders(
    institution_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user),
):
    viewer_id = current_user.id if current_user else None
    return reminder_service.list_reminders_out(db, viewer_id, institution_id)



@router.post("/", response_model=ReminderOut, status_code=201)
def create_reminder(
    data: ReminderCreate,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user),
):
    reminder = reminder_service.create(
        db,
        data,
        current_user.id if current_user else None,
    )
    out = reminder_service.single_reminder_out(
        db,
        reminder.id,
        current_user.id if current_user else None,
    )
    if not out:
        raise HTTPException(status_code=500, detail="Failed to load reminder")
    return out


@router.put("/{reminder_id}", response_model=ReminderOut)
def update_reminder(
    reminder_id: int,
    data: ReminderUpdate,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user),
):
    reminder = reminder_service.get_by_id(db, reminder_id)
    if not reminder:
        raise HTTPException(status_code=404, detail="Reminder not found")
    reminder_service.update(db, reminder, data)
    out = reminder_service.single_reminder_out(
        db,
        reminder_id,
        current_user.id if current_user else None,
    )
    if not out:
        raise HTTPException(status_code=404, detail="Reminder not found")
    return out


@router.delete("/{reminder_id}", status_code=204)
def delete_reminder(
    reminder_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    reminder = reminder_service.get_by_id(db, reminder_id)
    if not reminder:
        raise HTTPException(status_code=404, detail="Reminder not found")
    if not reminder_service.can_user_delete_reminder(current_user, reminder):
        raise HTTPException(
            status_code=403,
            detail="Você só pode remover lembretes que você criou.",
        )
    reminder_service.delete(db, reminder)

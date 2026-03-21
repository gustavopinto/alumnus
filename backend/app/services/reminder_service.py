import logging

from sqlalchemy.orm import Session

from ..models import Reminder
from ..schemas import ReminderCreate, ReminderUpdate

logger = logging.getLogger(__name__)


def list_ordered(db: Session) -> list[Reminder]:
    return (
        db.query(Reminder)
        .order_by(
            Reminder.done,
            Reminder.due_date.asc().nullslast(),
            Reminder.created_at.desc(),
        )
        .all()
    )


def create(
    db: Session,
    data: ReminderCreate,
    created_by_id: int | None,
) -> Reminder:
    reminder = Reminder(
        text=data.text,
        due_date=data.due_date or None,
        created_by_id=created_by_id,
    )
    db.add(reminder)
    db.commit()
    db.refresh(reminder)
    logger.info("Reminder created: id=%s", reminder.id)
    return reminder


def get_by_id(db: Session, reminder_id: int) -> Reminder | None:
    return db.query(Reminder).get(reminder_id)


def update(db: Session, reminder: Reminder, data: ReminderUpdate) -> Reminder:
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(reminder, key, value)
    db.commit()
    db.refresh(reminder)
    return reminder


def delete(db: Session, reminder: Reminder) -> None:
    db.delete(reminder)
    db.commit()
    logger.info("Reminder deleted: id=%s", reminder.id)

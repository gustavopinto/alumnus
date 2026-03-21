import logging

from sqlalchemy.orm import Session, joinedload

from ..models import Reminder, ReminderRead
from ..schemas import ReminderCreate, ReminderOut, ReminderUpdate

logger = logging.getLogger(__name__)


def _read_ids_for_user(db: Session, user_id: int) -> set[int]:
    return {
        row.reminder_id
        for row in db.query(ReminderRead.reminder_id)
        .filter(ReminderRead.user_id == user_id)
        .all()
    }


def reminder_to_out(
    r: Reminder,
    viewer_id: int | None,
    read_ids: set[int] | None = None,
) -> ReminderOut:
    created_by_name = r.created_by.nome if r.created_by else None
    notification_unread = False
    if (
        viewer_id is not None
        and r.created_by_id is not None
        and r.created_by_id != viewer_id
        and read_ids is not None
    ):
        notification_unread = r.id not in read_ids
    return ReminderOut(
        id=r.id,
        text=r.text,
        due_date=r.due_date,
        done=r.done,
        created_at=r.created_at,
        created_by_id=r.created_by_id,
        created_by_name=created_by_name,
        notification_unread=notification_unread,
    )


def list_ordered(db: Session) -> list[Reminder]:
    return (
        db.query(Reminder)
        .options(joinedload(Reminder.created_by))
        .order_by(
            Reminder.done,
            Reminder.due_date.asc().nullslast(),
            Reminder.created_at.desc(),
        )
        .all()
    )


def list_reminders_out(db: Session, viewer_id: int | None) -> list[ReminderOut]:
    reminders = list_ordered(db)
    read_ids: set[int] | None = None
    if viewer_id is not None:
        read_ids = _read_ids_for_user(db, viewer_id)
    else:
        read_ids = set()
    return [reminder_to_out(r, viewer_id, read_ids) for r in reminders]


def count_unread_notifications(db: Session, user_id: int) -> int:
    read_subq = (
        db.query(ReminderRead.reminder_id).filter(ReminderRead.user_id == user_id)
    )
    return (
        db.query(Reminder)
        .filter(
            Reminder.created_by_id.isnot(None),
            Reminder.created_by_id != user_id,
            ~Reminder.id.in_(read_subq),
        )
        .count()
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
    return (
        db.query(Reminder)
        .options(joinedload(Reminder.created_by))
        .filter(Reminder.id == reminder_id)
        .first()
    )


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


def mark_notification_read(db: Session, user_id: int, reminder_id: int) -> bool:
    reminder = get_by_id(db, reminder_id)
    if not reminder:
        return False
    if reminder.created_by_id is None or reminder.created_by_id == user_id:
        return True
    existing = (
        db.query(ReminderRead)
        .filter(
            ReminderRead.user_id == user_id,
            ReminderRead.reminder_id == reminder_id,
        )
        .first()
    )
    if existing:
        return True
    db.add(ReminderRead(user_id=user_id, reminder_id=reminder_id))
    db.commit()
    return True


def single_reminder_out(db: Session, reminder_id: int, viewer_id: int | None) -> ReminderOut | None:
    r = get_by_id(db, reminder_id)
    if not r:
        return None
    read_ids: set[int] = set()
    if viewer_id is not None:
        read_ids = _read_ids_for_user(db, viewer_id)
    return reminder_to_out(r, viewer_id, read_ids)

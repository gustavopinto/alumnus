import logging
import re

from sqlalchemy.orm import Session, joinedload

from ..models import Reminder, ReminderRead, User, Researcher
from ..schemas import ReminderCreate, ReminderOut, ReminderUpdate
from ..slug import slugify

logger = logging.getLogger(__name__)


def _extract_mention_slugs(text: str) -> set[str]:
    return set(re.findall(r'@([\w-]+)', text))


def _find_users_for_mentions(db: Session, slugs: set[str]) -> list[User]:
    if not slugs:
        return []
    researchers = db.query(Researcher).all()
    matched_ids = {r.id for r in researchers if slugify(r.nome) in slugs}
    if not matched_ids:
        return []
    return db.query(User).filter(User.researcher_id.in_(matched_ids)).all()


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
    creator_name_map: dict[int, str] | None = None,
) -> ReminderOut:
    created_by_name = None
    if r.created_by_id is not None:
        if r.created_by is not None:
            created_by_name = r.created_by.nome
        elif creator_name_map:
            created_by_name = creator_name_map.get(r.created_by_id)
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
    creator_ids = {r.created_by_id for r in reminders if r.created_by_id is not None}
    creator_name_map: dict[int, str] = {}
    if creator_ids:
        for uid, nome in db.query(User.id, User.nome).filter(User.id.in_(creator_ids)).all():
            creator_name_map[uid] = nome
    return [reminder_to_out(r, viewer_id, read_ids, creator_name_map) for r in reminders]


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

    # Create a copy for each mentioned user (@slug)
    if created_by_id is not None:
        slugs = _extract_mention_slugs(data.text)
        if slugs:
            mentioned_users = _find_users_for_mentions(db, slugs)
            copies = 0
            for u in mentioned_users:
                if u.id != created_by_id:
                    db.add(Reminder(
                        text=data.text,
                        due_date=data.due_date or None,
                        created_by_id=created_by_id,
                    ))
                    copies += 1
            if copies:
                db.commit()
                logger.info("Reminder %s: created %s mention copies", reminder.id, copies)

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


def can_user_delete_reminder(user: User, reminder: Reminder) -> bool:
    """Criador remove o próprio lembrete; sem criador (legado), só professor."""
    if reminder.created_by_id is None:
        return user.role in ("professor", "admin")
    return reminder.created_by_id == user.id


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
    creator_name_map = None
    if r.created_by_id is not None and r.created_by is None:
        u = db.query(User).filter(User.id == r.created_by_id).first()
        creator_name_map = {u.id: u.nome} if u else {}
    return reminder_to_out(r, viewer_id, read_ids, creator_name_map)

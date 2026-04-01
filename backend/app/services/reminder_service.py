import logging

from sqlalchemy.orm import Session, joinedload

from ..models import Reminder, User
from ..schemas import ReminderCreate, ReminderOut, ReminderUpdate

logger = logging.getLogger(__name__)



def reminder_to_out(
    r: Reminder,
    viewer_id: int | None,
    creator_name_map: dict[int, str] | None = None,
) -> ReminderOut:
    created_by_name = None
    if r.created_by_id is not None:
        if r.created_by is not None:
            created_by_name = r.created_by.nome
        elif creator_name_map:
            created_by_name = creator_name_map.get(r.created_by_id)
    return ReminderOut(
        id=r.id,
        text=r.text,
        due_date=r.due_date,
        done=r.done,
        created_at=r.created_at,
        created_by_id=r.created_by_id,
        created_by_name=created_by_name,
        institution_id=r.institution_id,
    )


def list_ordered(db: Session, institution_id: int | None = None) -> list[Reminder]:
    q = db.query(Reminder).options(joinedload(Reminder.created_by))
    if institution_id is not None:
        q = q.filter(Reminder.institution_id == institution_id)
    return q.order_by(
        Reminder.done,
        Reminder.due_date.asc().nullslast(),
        Reminder.created_at.desc(),
    ).all()


def list_reminders_out(db: Session, viewer_id: int | None, institution_id: int | None = None) -> list[ReminderOut]:
    # created_by já está carregado via joinedload em list_ordered — query extra desnecessária
    reminders = list_ordered(db, institution_id)
    return [reminder_to_out(r, viewer_id) for r in reminders]


def create(
    db: Session,
    data: ReminderCreate,
    created_by_id: int | None,
) -> Reminder:
    reminder = Reminder(
        text=data.text,
        due_date=data.due_date or None,
        created_by_id=created_by_id,
        institution_id=data.institution_id,
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


def can_user_delete_reminder(user: User, reminder: Reminder) -> bool:
    """Privilegiados removem qualquer lembrete; aluno só remove o próprio."""
    if user.role in ("professor", "admin", "superadmin"):
        return True
    return reminder.created_by_id == user.id


def delete(db: Session, reminder: Reminder) -> None:
    db.delete(reminder)
    db.commit()
    logger.info("Reminder deleted: id=%s", reminder.id)


def single_reminder_out(db: Session, reminder_id: int, viewer_id: int | None) -> ReminderOut | None:
    r = get_by_id(db, reminder_id)
    if not r:
        return None
    creator_name_map = None
    if r.created_by_id is not None and r.created_by is None:
        u = db.query(User).filter(User.id == r.created_by_id).first()
        creator_name_map = {u.id: u.nome} if u else {}
    return reminder_to_out(r, viewer_id, creator_name_map)

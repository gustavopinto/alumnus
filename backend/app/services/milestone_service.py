import logging

from sqlalchemy.orm import Session

from ..models import Milestone
from ..schemas import MilestoneCreate, MilestoneUpdate

logger = logging.getLogger(__name__)


def list_by_user(db: Session, user_id: int) -> list[Milestone]:
    return (
        db.query(Milestone)
        .filter(Milestone.user_id == user_id)
        .order_by(Milestone.date.asc())
        .all()
    )


def get_by_id(db: Session, milestone_id: int) -> Milestone | None:
    return db.query(Milestone).filter(Milestone.id == milestone_id).first()


def create(db: Session, user_id: int, data: MilestoneCreate, created_by_id: int | None) -> Milestone:
    m = Milestone(
        user_id=user_id,
        created_by_id=created_by_id,
        **data.model_dump(),
    )
    db.add(m)
    db.commit()
    db.refresh(m)
    logger.info("Milestone created: id=%s user_id=%s", m.id, user_id)
    return m


def update(db: Session, milestone: Milestone, data: MilestoneUpdate) -> Milestone:
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(milestone, key, value)
    db.commit()
    db.refresh(milestone)
    return milestone


def delete(db: Session, milestone: Milestone) -> None:
    db.delete(milestone)
    db.commit()
    logger.info("Milestone deleted: id=%s", milestone.id)

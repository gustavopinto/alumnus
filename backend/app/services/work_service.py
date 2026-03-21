import logging

from sqlalchemy.orm import Session

from ..models import Work
from ..schemas import WorkCreate, WorkUpdate

logger = logging.getLogger(__name__)


def list_by_researcher(db: Session, researcher_id: int) -> list[Work]:
    return (
        db.query(Work)
        .filter(Work.researcher_id == researcher_id)
        .order_by(Work.year.desc(), Work.id.desc())
        .all()
    )


def create(db: Session, researcher_id: int, data: WorkCreate) -> Work:
    work = Work(researcher_id=researcher_id, **data.model_dump())
    db.add(work)
    db.commit()
    db.refresh(work)
    logger.info("Work created: %s (%s) for researcher %s", work.title, work.type, researcher_id)
    return work


def get_by_id(db: Session, work_id: int) -> Work | None:
    return db.query(Work).get(work_id)


def update(db: Session, work: Work, data: WorkUpdate) -> Work:
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(work, key, value)
    db.commit()
    db.refresh(work)
    return work


def delete(db: Session, work: Work) -> None:
    db.delete(work)
    db.commit()
    logger.info("Work deleted: id=%s", work.id)

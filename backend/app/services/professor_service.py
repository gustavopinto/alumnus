import logging

from sqlalchemy.orm import Session

from ..models import Professor, User

logger = logging.getLogger(__name__)


def get_by_id(db: Session, professor_id: int) -> Professor | None:
    return db.query(Professor).get(professor_id)


def get_by_user(db: Session, user: User) -> Professor | None:
    if not user.professor_id:
        return None
    return get_by_id(db, user.professor_id)


def list_active(db: Session) -> list[Professor]:
    return db.query(Professor).filter(Professor.ativo == True).order_by(Professor.nome).all()


def update(db: Session, professor: Professor, data: dict) -> Professor:
    for key, value in data.items():
        if hasattr(professor, key):
            setattr(professor, key, value)
    db.commit()
    db.refresh(professor)
    logger.info("Professor updated: id=%s", professor.id)
    return professor


def deactivate(db: Session, professor: Professor) -> None:
    professor.ativo = False
    db.commit()
    logger.info("Professor deactivated: id=%s", professor.id)

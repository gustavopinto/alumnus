import logging

from sqlalchemy.orm import Session

from ..models import Researcher, User
from ..schemas import ResearcherCreate, ResearcherUpdate
from ..slug import slugify

logger = logging.getLogger(__name__)


def list_all(db: Session, ativo: bool | None) -> list[Researcher]:
    q = db.query(Researcher)
    if ativo is not None:
        q = q.filter(Researcher.ativo == ativo)
    return q.order_by(Researcher.nome).all()


def create(db: Session, data: ResearcherCreate) -> Researcher:
    researcher = Researcher(**data.model_dump())
    db.add(researcher)
    db.commit()
    db.refresh(researcher)
    logger.info("Researcher created: %s (id=%s)", researcher.nome, researcher.id)
    return researcher


def get_by_id(db: Session, researcher_id: int) -> Researcher | None:
    return db.query(Researcher).get(researcher_id)


def find_by_slug(db: Session, slug: str) -> Researcher | None:
    researchers = db.query(Researcher).filter(Researcher.ativo == True).all()
    for r in researchers:
        if slugify(r.nome) == slug:
            return r
    return None


def get_linked_user(db: Session, researcher_id: int) -> User | None:
    return db.query(User).filter(User.researcher_id == researcher_id).first()


def update(db: Session, researcher: Researcher, data: ResearcherUpdate) -> Researcher:
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(researcher, key, value)
    db.commit()
    db.refresh(researcher)
    logger.info("Researcher updated: id=%s", researcher.id)
    return researcher


def deactivate(db: Session, researcher: Researcher) -> None:
    researcher.ativo = False
    db.commit()
    logger.info("Researcher deactivated: id=%s", researcher.id)

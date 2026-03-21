import logging

from sqlalchemy.orm import Session

from ..models import Relationship
from ..schemas import RelationshipCreate, RelationshipUpdate

logger = logging.getLogger(__name__)


def list_all(db: Session) -> list[Relationship]:
    return db.query(Relationship).all()


def create(db: Session, data: RelationshipCreate) -> Relationship:
    rel = Relationship(**data.model_dump())
    db.add(rel)
    db.commit()
    db.refresh(rel)
    logger.info(
        "Relationship created: %s -> %s (%s)",
        rel.source_researcher_id,
        rel.target_researcher_id,
        rel.relation_type,
    )
    return rel


def get_by_id(db: Session, rel_id: int) -> Relationship | None:
    return db.query(Relationship).get(rel_id)


def update(db: Session, rel: Relationship, data: RelationshipUpdate) -> Relationship:
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(rel, key, value)
    db.commit()
    db.refresh(rel)
    return rel


def delete(db: Session, rel: Relationship) -> None:
    db.delete(rel)
    db.commit()
    logger.info("Relationship deleted: id=%s", rel.id)

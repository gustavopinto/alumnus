import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Relationship
from ..schemas import RelationshipCreate, RelationshipUpdate, RelationshipOut

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/relationships", tags=["relationships"])


@router.get("/", response_model=list[RelationshipOut])
def list_relationships(db: Session = Depends(get_db)):
    return db.query(Relationship).all()


@router.post("/", response_model=RelationshipOut, status_code=201)
def create_relationship(data: RelationshipCreate, db: Session = Depends(get_db)):
    rel = Relationship(**data.model_dump())
    db.add(rel)
    db.commit()
    db.refresh(rel)
    logger.info("Relationship created: %s -> %s (%s)", rel.source_researcher_id, rel.target_researcher_id, rel.relation_type)
    return rel


@router.put("/{rel_id}", response_model=RelationshipOut)
def update_relationship(rel_id: int, data: RelationshipUpdate, db: Session = Depends(get_db)):
    rel = db.query(Relationship).get(rel_id)
    if not rel:
        raise HTTPException(status_code=404, detail="Relationship not found")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(rel, key, value)
    db.commit()
    db.refresh(rel)
    return rel


@router.delete("/{rel_id}", status_code=204)
def delete_relationship(rel_id: int, db: Session = Depends(get_db)):
    rel = db.query(Relationship).get(rel_id)
    if not rel:
        raise HTTPException(status_code=404, detail="Relationship not found")
    db.delete(rel)
    db.commit()
    logger.info("Relationship deleted: id=%s", rel_id)

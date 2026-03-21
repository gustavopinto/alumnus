import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..schemas import RelationshipCreate, RelationshipUpdate, RelationshipOut
from ..services import relationship_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/relationships", tags=["relationships"])


@router.get("/", response_model=list[RelationshipOut])
def list_relationships(db: Session = Depends(get_db)):
    return relationship_service.list_all(db)


@router.post("/", response_model=RelationshipOut, status_code=201)
def create_relationship(data: RelationshipCreate, db: Session = Depends(get_db)):
    return relationship_service.create(db, data)


@router.put("/{rel_id}", response_model=RelationshipOut)
def update_relationship(rel_id: int, data: RelationshipUpdate, db: Session = Depends(get_db)):
    rel = relationship_service.get_by_id(db, rel_id)
    if not rel:
        raise HTTPException(status_code=404, detail="Relationship not found")
    return relationship_service.update(db, rel, data)


@router.delete("/{rel_id}", status_code=204)
def delete_relationship(rel_id: int, db: Session = Depends(get_db)):
    rel = relationship_service.get_by_id(db, rel_id)
    if not rel:
        raise HTTPException(status_code=404, detail="Relationship not found")
    relationship_service.delete(db, rel)

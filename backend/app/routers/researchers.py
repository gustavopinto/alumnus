import logging

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Researcher, User
from ..schemas import ResearcherCreate, ResearcherUpdate, ResearcherOut, UserOut
from ..slug import slugify

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/researchers", tags=["researchers"])


@router.get("/", response_model=list[ResearcherOut])
def list_researchers(ativo: bool | None = None, db: Session = Depends(get_db)):
    query = db.query(Researcher)
    if ativo is not None:
        query = query.filter(Researcher.ativo == ativo)
    return query.order_by(Researcher.nome).all()


@router.post("/", response_model=ResearcherOut, status_code=201)
def create_researcher(data: ResearcherCreate, db: Session = Depends(get_db)):
    researcher = Researcher(**data.model_dump())
    db.add(researcher)
    db.commit()
    db.refresh(researcher)
    logger.info("Researcher created: %s (id=%s)", researcher.nome, researcher.id)
    return researcher


@router.get("/by-slug/{slug}", response_model=ResearcherOut)
def get_researcher_by_slug(slug: str, db: Session = Depends(get_db)):
    researchers = db.query(Researcher).filter(Researcher.ativo == True).all()
    for r in researchers:
        if slugify(r.nome) == slug:
            return r
    raise HTTPException(status_code=404, detail="Researcher not found")


@router.get("/{researcher_id}", response_model=ResearcherOut)
def get_researcher(researcher_id: int, db: Session = Depends(get_db)):
    researcher = db.query(Researcher).get(researcher_id)
    if not researcher:
        raise HTTPException(status_code=404, detail="Researcher not found")
    return researcher


@router.get("/{researcher_id}/user", response_model=Optional[UserOut])
def get_researcher_user(researcher_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.researcher_id == researcher_id).first()
    return user


@router.put("/{researcher_id}", response_model=ResearcherOut)
def update_researcher(researcher_id: int, data: ResearcherUpdate, db: Session = Depends(get_db)):
    researcher = db.query(Researcher).get(researcher_id)
    if not researcher:
        raise HTTPException(status_code=404, detail="Researcher not found")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(researcher, key, value)
    db.commit()
    db.refresh(researcher)
    logger.info("Researcher updated: id=%s", researcher.id)
    return researcher


@router.delete("/{researcher_id}", status_code=204)
def deactivate_researcher(researcher_id: int, db: Session = Depends(get_db)):
    researcher = db.query(Researcher).get(researcher_id)
    if not researcher:
        raise HTTPException(status_code=404, detail="Researcher not found")
    researcher.ativo = False
    db.commit()
    logger.info("Researcher deactivated: id=%s", researcher_id)

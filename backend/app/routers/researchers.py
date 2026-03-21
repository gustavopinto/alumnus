import logging

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import User
from ..schemas import ResearcherCreate, ResearcherUpdate, ResearcherOut, UserOut
from ..deps import get_current_user
from ..plan import refresh_user_plan_status, user_to_out
from ..services import researcher_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/researchers", tags=["researchers"])


@router.get("/", response_model=list[ResearcherOut])
def list_researchers(ativo: bool | None = None, db: Session = Depends(get_db)):
    return researcher_service.list_all(db, ativo)


@router.post("/", response_model=ResearcherOut, status_code=201)
def create_researcher(data: ResearcherCreate, db: Session = Depends(get_db)):
    return researcher_service.create(db, data)


@router.get("/by-slug/{slug}", response_model=ResearcherOut)
def get_researcher_by_slug(slug: str, db: Session = Depends(get_db)):
    r = researcher_service.find_by_slug(db, slug)
    if not r:
        raise HTTPException(status_code=404, detail="Researcher not found")
    return r


@router.get("/{researcher_id}", response_model=ResearcherOut)
def get_researcher(researcher_id: int, db: Session = Depends(get_db)):
    researcher = researcher_service.get_by_id(db, researcher_id)
    if not researcher:
        raise HTTPException(status_code=404, detail="Researcher not found")
    return researcher


@router.get("/{researcher_id}/user", response_model=Optional[UserOut])
def get_researcher_user(researcher_id: int, db: Session = Depends(get_db)):
    u = researcher_service.get_linked_user(db, researcher_id)
    if not u:
        return None
    refresh_user_plan_status(db, u)
    db.refresh(u)
    return user_to_out(u)


@router.put("/{researcher_id}", response_model=ResearcherOut)
def update_researcher(
    researcher_id: int,
    data: ResearcherUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    researcher = researcher_service.get_by_id(db, researcher_id)
    if not researcher:
        raise HTTPException(status_code=404, detail="Researcher not found")
    is_own = current_user.researcher_id == researcher_id
    if current_user.role not in ("professor", "admin", "superadmin") and not is_own:
        raise HTTPException(status_code=403, detail="Você só pode editar o seu próprio perfil")
    return researcher_service.update(db, researcher, data)


@router.delete("/{researcher_id}", status_code=204)
def deactivate_researcher(researcher_id: int, db: Session = Depends(get_db)):
    researcher = researcher_service.get_by_id(db, researcher_id)
    if not researcher:
        raise HTTPException(status_code=404, detail="Researcher not found")
    researcher_service.deactivate(db, researcher)

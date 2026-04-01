import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_current_user
from ..models import User
from ..schemas import MilestoneCreate, MilestoneOut, MilestoneUpdate
from ..services import milestone_service, researcher_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/researchers/{researcher_id}/milestones", tags=["milestones"])


def _get_researcher_or_404(researcher_id: int, db: Session):
    r = researcher_service.get_by_id(db, researcher_id)
    if not r:
        raise HTTPException(status_code=404, detail="Researcher not found")
    return r


def _check_can_edit(current_user: User, researcher_id: int):
    is_own = current_user.researcher_id == researcher_id
    if current_user.role not in ("professor", "superadmin") and not is_own:
        raise HTTPException(status_code=403, detail="Sem permissão para editar marcos deste pesquisador")


@router.get("/", response_model=list[MilestoneOut])
def list_milestones(
    researcher_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    _get_researcher_or_404(researcher_id, db)
    return milestone_service.list_by_researcher(db, researcher_id)


@router.post("/", response_model=MilestoneOut, status_code=201)
def create_milestone(
    researcher_id: int,
    data: MilestoneCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _get_researcher_or_404(researcher_id, db)
    _check_can_edit(current_user, researcher_id)
    return milestone_service.create(db, researcher_id, data, current_user.id)


@router.put("/{milestone_id}", response_model=MilestoneOut)
def update_milestone(
    researcher_id: int,
    milestone_id: int,
    data: MilestoneUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _get_researcher_or_404(researcher_id, db)
    _check_can_edit(current_user, researcher_id)
    milestone = milestone_service.get_by_id(db, milestone_id)
    if not milestone or milestone.researcher_id != researcher_id:
        raise HTTPException(status_code=404, detail="Marco não encontrado")
    return milestone_service.update(db, milestone, data)


@router.delete("/{milestone_id}", status_code=204)
def delete_milestone(
    researcher_id: int,
    milestone_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _get_researcher_or_404(researcher_id, db)
    _check_can_edit(current_user, researcher_id)
    milestone = milestone_service.get_by_id(db, milestone_id)
    if not milestone or milestone.researcher_id != researcher_id:
        raise HTTPException(status_code=404, detail="Marco não encontrado")
    milestone_service.delete(db, milestone)

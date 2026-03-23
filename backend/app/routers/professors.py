from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import require_professor, require_dashboard
from ..models import User
from ..schemas import ProfessorOut, ProfessorUpdate
from ..services import professor_service

router = APIRouter(prefix="/professors", tags=["professors"])


@router.get("/", response_model=list[ProfessorOut])
def list_professors(
    db: Session = Depends(get_db),
    _: User = Depends(require_dashboard),
):
    return professor_service.list_active(db)


@router.get("/{professor_id}", response_model=ProfessorOut)
def get_professor(
    professor_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_dashboard),
):
    p = professor_service.get_by_id(db, professor_id)
    if not p:
        raise HTTPException(status_code=404, detail="Professor não encontrado")
    return p


@router.put("/{professor_id}", response_model=ProfessorOut)
def update_professor(
    professor_id: int,
    data: ProfessorUpdate,
    db: Session = Depends(get_db),
    current: User = Depends(require_professor),
):
    p = professor_service.get_by_id(db, professor_id)
    if not p:
        raise HTTPException(status_code=404, detail="Professor não encontrado")
    # Apenas o próprio professor ou superadmin pode editar
    if current.role != "superadmin" and current.professor_id != professor_id:
        raise HTTPException(status_code=403, detail="Sem permissão para editar este professor")
    return professor_service.update(db, p, data.model_dump(exclude_unset=True))

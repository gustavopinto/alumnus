from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import require_professor, require_superadmin, get_current_user
from ..models import ProfessorGroup, ResearchGroup, Researcher, User
from ..schemas import JoinGroupRequest, ResearchGroupCreate, ResearchGroupOut, ResearchGroupUpdate
from ..services import group_service, professor_service

router = APIRouter(prefix="/groups", tags=["groups"])


def _group_out(group: ResearchGroup) -> dict:
    return {
        "id":               group.id,
        "name":             group.name,
        "institution_id":   group.institution_id,
        "institution_name": group.institution.name if group.institution else None,
        "created_at":       group.created_at,
    }


@router.get("/", response_model=list[ResearchGroupOut])
def list_my_groups(
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
):
    """Lista os grupos do professor logado. Superadmin lista todos. Aluno retorna seu próprio grupo."""
    if current.role == "superadmin":
        groups = db.query(ResearchGroup).order_by(ResearchGroup.name).all()
    elif current.role == "professor":
        professor = professor_service.get_by_user(db, current)
        if not professor:
            return []
        groups = group_service.list_professor_groups(db, professor)
    else:
        # Student: retorna apenas o grupo ao qual pertence
        if current.researcher and current.researcher.group_id:
            group = group_service.get_group_by_id(db, current.researcher.group_id)
            groups = [group] if group else []
        else:
            groups = []
    return [_group_out(g) for g in groups]


@router.post("/", response_model=ResearchGroupOut, status_code=201)
def create_group(
    data: ResearchGroupCreate,
    db: Session = Depends(get_db),
    current: User = Depends(require_professor),
):
    if current.role == "superadmin":
        professor = professor_service.get_by_user(db, current)
        if not professor:
            # Superadmin without a professor record: create the group directly
            group = group_service.create_group_direct(db, data.name, data.institution_id)
            return _group_out(group)
    else:
        professor = professor_service.get_by_user(db, current)
        if not professor:
            raise HTTPException(status_code=403, detail="Perfil de professor não encontrado")
    group = group_service.create_group(db, professor, data.name, data.institution_id)
    return _group_out(group)


@router.patch("/{group_id}", response_model=ResearchGroupOut)
def update_group(
    group_id: int,
    data: ResearchGroupUpdate,
    db: Session = Depends(get_db),
    current: User = Depends(require_professor),
):
    group = group_service.get_group_by_id(db, group_id)
    if not group:
        raise HTTPException(status_code=404, detail="Grupo não encontrado")

    # Verifica que o usuário é coordinator do grupo
    if current.role != "superadmin":
        professor = professor_service.get_by_user(db, current)
        if not professor:
            raise HTTPException(status_code=403, detail="Perfil de professor não encontrado")
        pg = db.query(ProfessorGroup).filter(
            ProfessorGroup.professor_id == professor.id,
            ProfessorGroup.group_id == group_id,
            ProfessorGroup.role_in_group == "coordinator",
        ).first()
        if not pg:
            raise HTTPException(status_code=403, detail="Apenas o coordinator pode editar o grupo")

    updated = group_service.update_group(db, group, data.model_dump(exclude_unset=True))
    return _group_out(updated)


@router.post("/{group_id}/join", status_code=200)
def join_group(
    group_id: int,
    data: JoinGroupRequest,
    db: Session = Depends(get_db),
    current: User = Depends(require_professor),
):
    professor = professor_service.get_by_user(db, current)
    if not professor:
        raise HTTPException(status_code=403, detail="Perfil de professor não encontrado")
    try:
        pg = group_service.join_group(db, professor, group_id, data.institution_id)
    except ValueError as e:
        msgs = {
            "sem_vinculo_instituicao": "Professor não tem vínculo com esta instituição",
            "ja_membro": "Professor já é membro deste grupo",
            "grupo_nao_encontrado": "Grupo não encontrado",
        }
        raise HTTPException(status_code=400, detail=msgs.get(str(e), str(e)))
    return {"professor_id": pg.professor_id, "group_id": pg.group_id, "role": pg.role_in_group}


@router.delete("/{group_id}/leave", status_code=204)
def leave_group(
    group_id: int,
    db: Session = Depends(get_db),
    current: User = Depends(require_professor),
):
    professor = professor_service.get_by_user(db, current)
    if not professor:
        raise HTTPException(status_code=403, detail="Perfil de professor não encontrado")
    try:
        group_service.leave_group(db, professor, group_id)
    except ValueError as e:
        msgs = {
            "nao_membro":         "Professor não é membro deste grupo",
            "unico_coordinator":  "Não é possível sair: você é o único coordinator do grupo",
        }
        raise HTTPException(status_code=400, detail=msgs.get(str(e), str(e)))


@router.get("/{group_id}/members")
def list_group_members(
    group_id: int,
    db: Session = Depends(get_db),
    current: User = Depends(require_professor),
):
    group = group_service.get_group_by_id(db, group_id)
    if not group:
        raise HTTPException(status_code=404, detail="Grupo não encontrado")

    researchers = (
        db.query(Researcher)
        .outerjoin(User, User.researcher_id == Researcher.id)
        .filter(Researcher.group_id == group_id, User.ativo == True)
        .order_by(User.nome)
        .all()
    )

    return [
        {
            "id":         r.id,
            "nome":       r.nome,
            "status":     r.status,
            "registered": r.registered,
            "email":      r.email,
        }
        for r in researchers
    ]

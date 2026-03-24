from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import require_professor, require_superadmin
from ..models import User
from ..schemas import AddInstitutionalEmail, InstitutionOut, ProfessorInstitutionOut
from ..services import institution_service, professor_service
from ..institutional_email import INSTITUTIONAL_EMAIL_HELP_PT

router = APIRouter(prefix="/institutions", tags=["institutions"])


@router.get("/", response_model=list[InstitutionOut])
def list_institutions(
    db: Session = Depends(get_db),
    _: User = Depends(require_superadmin),
):
    return institution_service.list_all(db)


@router.post("/", response_model=InstitutionOut, status_code=201)
def create_institution(
    data: AddInstitutionalEmail,
    db: Session = Depends(get_db),
    _: User = Depends(require_superadmin),
):
    from ..institutional_email import extract_domain, is_public_email_domain
    if is_public_email_domain(data.email):
        raise HTTPException(status_code=422, detail=INSTITUTIONAL_EMAIL_HELP_PT)
    domain = extract_domain(data.email)
    inst = institution_service.get_or_create_institution(db, domain)
    from ..models import ResearchGroup
    existing_group = db.query(ResearchGroup).filter(ResearchGroup.institution_id == inst.id).first()
    if not existing_group:
        group = ResearchGroup(name=f"Grupo {inst.name}", institution_id=inst.id)
        db.add(group)
    db.commit()
    db.refresh(inst)
    return inst


# ── Emails institucionais do professor ────────────────────────────────────────

@router.get("/my-emails", response_model=list[ProfessorInstitutionOut])
def list_my_emails(
    db: Session = Depends(get_db),
    current: User = Depends(require_professor),
):
    professor = professor_service.get_by_user(db, current)
    if not professor:
        raise HTTPException(status_code=404, detail="Perfil de professor não encontrado")
    items = institution_service.list_professor_emails(db, professor)
    return [
        ProfessorInstitutionOut(
            id=pi.id,
            professor_id=pi.professor_id,
            institution_id=pi.institution_id,
            institutional_email=pi.institutional_email,
            institution_name=pi.institution.name if pi.institution else None,
            institution_domain=pi.institution.domain if pi.institution else None,
            created_at=pi.created_at,
        )
        for pi in items
    ]


@router.post("/my-emails", response_model=ProfessorInstitutionOut, status_code=201)
def add_my_email(
    data: AddInstitutionalEmail,
    db: Session = Depends(get_db),
    current: User = Depends(require_professor),
):
    professor = professor_service.get_by_user(db, current)
    if not professor:
        raise HTTPException(status_code=404, detail="Perfil de professor não encontrado")
    try:
        pi = institution_service.add_institutional_email(db, professor, data.email)
    except ValueError as e:
        msgs = {
            "email_publico":        INSTITUTIONAL_EMAIL_HELP_PT,
            "email_duplicado":      "Este email já está cadastrado para outro professor",
            "instituicao_duplicada": "Você já tem um email cadastrado nesta instituição",
        }
        raise HTTPException(status_code=409 if "duplicado" in str(e) else 422,
                            detail=msgs.get(str(e), str(e)))
    return ProfessorInstitutionOut(
        id=pi.id,
        professor_id=pi.professor_id,
        institution_id=pi.institution_id,
        institutional_email=pi.institutional_email,
        institution_name=pi.institution.name if pi.institution else None,
        institution_domain=pi.institution.domain if pi.institution else None,
        created_at=pi.created_at,
    )


@router.delete("/my-emails/{pi_id}", status_code=204)
def remove_my_email(
    pi_id: int,
    db: Session = Depends(get_db),
    current: User = Depends(require_professor),
):
    professor = professor_service.get_by_user(db, current)
    if not professor:
        raise HTTPException(status_code=404, detail="Perfil de professor não encontrado")
    try:
        institution_service.remove_institutional_email(db, professor, pi_id)
    except ValueError as e:
        msgs = {
            "minimo_um_email": "Você deve manter ao menos um email institucional",
            "nao_encontrado":  "Email não encontrado",
        }
        raise HTTPException(status_code=400, detail=msgs.get(str(e), str(e)))

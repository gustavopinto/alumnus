import logging

from sqlalchemy.orm import Session

from ..institutional_email import extract_domain, is_public_email_domain
from ..models import Institution, Professor, ProfessorInstitution, ProfessorGroup, ResearchGroup

logger = logging.getLogger(__name__)


def get_or_create_institution(db: Session, domain: str) -> Institution:
    """Retorna a instituição pelo domínio, criando se não existir."""
    inst = db.query(Institution).filter(Institution.domain == domain).first()
    if not inst:
        name = domain.split(".")[0].upper()
        inst = Institution(name=name, domain=domain)
        db.add(inst)
        db.flush()
        logger.info("Institution created: domain=%s", domain)
    return inst


def list_all(db: Session) -> list[Institution]:
    return db.query(Institution).order_by(Institution.name).all()


def get_by_id(db: Session, institution_id: int) -> Institution | None:
    return db.query(Institution).get(institution_id)


def list_professor_emails(db: Session, professor: Professor) -> list[ProfessorInstitution]:
    return (
        db.query(ProfessorInstitution)
        .filter(ProfessorInstitution.professor_id == professor.id)
        .order_by(ProfessorInstitution.created_at)
        .all()
    )


def add_institutional_email(
    db: Session,
    professor: Professor,
    email: str,
) -> ProfessorInstitution:
    """Valida e adiciona um email institucional ao professor."""
    if is_public_email_domain(email):
        raise ValueError("email_publico")

    # Unicidade global
    existing = db.query(ProfessorInstitution).filter(
        ProfessorInstitution.institutional_email == email
    ).first()
    if existing:
        raise ValueError("email_duplicado")

    domain = extract_domain(email)
    institution = get_or_create_institution(db, domain)

    # Verifica se já tem vínculo com essa instituição
    link = db.query(ProfessorInstitution).filter(
        ProfessorInstitution.professor_id == professor.id,
        ProfessorInstitution.institution_id == institution.id,
    ).first()
    if link:
        raise ValueError("instituicao_duplicada")

    pi = ProfessorInstitution(
        professor_id=professor.id,
        institution_id=institution.id,
        institutional_email=email,
    )
    db.add(pi)
    # Auto-create a group for this institution+professor if none exists
    existing_pg = db.query(ProfessorGroup).filter(
        ProfessorGroup.professor_id == professor.id,
        ProfessorGroup.institution_id == institution.id,
    ).first()
    if not existing_pg:
        group = ResearchGroup(name=f"Grupo {institution.name}", institution_id=institution.id)
        db.add(group)
        db.flush()
        pg = ProfessorGroup(
            professor_id=professor.id,
            group_id=group.id,
            role_in_group="coordinator",
            institution_id=institution.id,
        )
        db.add(pg)
    db.commit()
    db.refresh(pi)
    logger.info("ProfessorInstitution added: professor=%s email=%s", professor.id, email)
    return pi


def remove_institutional_email(
    db: Session,
    professor: Professor,
    pi_id: int,
) -> None:
    """Remove email institucional; garante que o professor mantém ao menos 1."""
    total = db.query(ProfessorInstitution).filter(
        ProfessorInstitution.professor_id == professor.id
    ).count()
    if total <= 1:
        raise ValueError("minimo_um_email")

    pi = db.query(ProfessorInstitution).filter(
        ProfessorInstitution.id == pi_id,
        ProfessorInstitution.professor_id == professor.id,
    ).first()
    if not pi:
        raise ValueError("nao_encontrado")

    db.delete(pi)
    db.commit()
    logger.info("ProfessorInstitution removed: id=%s", pi_id)

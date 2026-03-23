import logging

from sqlalchemy.orm import Session

from ..models import Professor, ProfessorGroup, ProfessorInstitution, ResearchGroup

logger = logging.getLogger(__name__)


def list_professor_groups(db: Session, professor: Professor) -> list[ResearchGroup]:
    ids = [pg.group_id for pg in professor.professor_groups]
    if not ids:
        return []
    return db.query(ResearchGroup).filter(ResearchGroup.id.in_(ids)).all()


def get_coordinator_group(db: Session, professor: Professor) -> ResearchGroup | None:
    """Retorna o grupo onde o professor é coordinator (o principal)."""
    pg = db.query(ProfessorGroup).filter(
        ProfessorGroup.professor_id == professor.id,
        ProfessorGroup.role_in_group == "coordinator",
    ).first()
    return pg.group if pg else None


def create_group(
    db: Session,
    professor: Professor,
    name: str,
    institution_id: int,
) -> ResearchGroup:
    """Cria grupo e adiciona o professor como coordinator."""
    group = ResearchGroup(name=name, institution_id=institution_id)
    db.add(group)
    db.flush()

    pg = ProfessorGroup(
        professor_id=professor.id,
        group_id=group.id,
        role_in_group="coordinator",
        institution_id=institution_id,
    )
    db.add(pg)
    db.commit()
    db.refresh(group)
    logger.info("ResearchGroup created: id=%s professor=%s", group.id, professor.id)
    return group


def create_group_direct(
    db: Session,
    name: str,
    institution_id: int,
) -> ResearchGroup:
    """Cria grupo sem professor associado (superadmin sem perfil de professor)."""
    group = ResearchGroup(name=name, institution_id=institution_id)
    db.add(group)
    db.commit()
    db.refresh(group)
    logger.info("ResearchGroup created (direct): id=%s", group.id)
    return group


def join_group(
    db: Session,
    professor: Professor,
    group_id: int,
    institution_id: int,
) -> ProfessorGroup:
    """Professor entra em um grupo existente como member."""
    # Valida que o professor tem vínculo com a instituição
    pi = db.query(ProfessorInstitution).filter(
        ProfessorInstitution.professor_id == professor.id,
        ProfessorInstitution.institution_id == institution_id,
    ).first()
    if not pi:
        raise ValueError("sem_vinculo_instituicao")

    existing = db.query(ProfessorGroup).filter(
        ProfessorGroup.professor_id == professor.id,
        ProfessorGroup.group_id == group_id,
    ).first()
    if existing:
        raise ValueError("ja_membro")

    group = db.query(ResearchGroup).get(group_id)
    if not group:
        raise ValueError("grupo_nao_encontrado")

    pg = ProfessorGroup(
        professor_id=professor.id,
        group_id=group_id,
        role_in_group="member",
        institution_id=institution_id,
    )
    db.add(pg)
    db.commit()
    db.refresh(pg)
    logger.info("Professor %s joined group %s", professor.id, group_id)
    return pg


def leave_group(db: Session, professor: Professor, group_id: int) -> None:
    """Professor sai de um grupo (não pode sair se for único coordinator)."""
    pg = db.query(ProfessorGroup).filter(
        ProfessorGroup.professor_id == professor.id,
        ProfessorGroup.group_id == group_id,
    ).first()
    if not pg:
        raise ValueError("nao_membro")

    if pg.role_in_group == "coordinator":
        other_coords = db.query(ProfessorGroup).filter(
            ProfessorGroup.group_id == group_id,
            ProfessorGroup.role_in_group == "coordinator",
            ProfessorGroup.professor_id != professor.id,
        ).count()
        if other_coords == 0:
            raise ValueError("unico_coordinator")

    db.delete(pg)
    db.commit()
    logger.info("Professor %s left group %s", professor.id, group_id)


def update_group(db: Session, group: ResearchGroup, data: dict) -> ResearchGroup:
    for key, value in data.items():
        if hasattr(group, key):
            setattr(group, key, value)
    db.commit()
    db.refresh(group)
    return group


def get_group_by_id(db: Session, group_id: int) -> ResearchGroup | None:
    return db.query(ResearchGroup).get(group_id)

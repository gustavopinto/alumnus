import logging

from sqlalchemy import or_
from sqlalchemy.orm import Session

from ..models import Professor, ProfessorInstitution, ResearchGroup, Researcher, User
from ..schemas import ResearcherCreate, ResearcherUpdate
from ..slug import slugify

logger = logging.getLogger(__name__)


def _resolve_group_id(db: Session, orientador_id: int | None) -> int | None:
    """Dado um professor orientador, retorna o group_id do seu grupo principal (coordinator)."""
    if orientador_id is None:
        return None
    pg = db.query(ProfessorGroup).filter(
        ProfessorGroup.professor_id == orientador_id,
        ProfessorGroup.role_in_group == "coordinator",
    ).first()
    return pg.group_id if pg else None


def list_all(db: Session, ativo: bool | None, institution_id: int | None = None) -> list[Researcher]:
    q = db.query(Researcher)
    if ativo is not None:
        q = q.filter(Researcher.ativo == ativo)
    if institution_id is not None:
        group_ids = db.query(ResearchGroup.id).filter(
            ResearchGroup.institution_id == institution_id
        ).subquery()
        prof_ids = db.query(ProfessorInstitution.professor_id).filter(
            ProfessorInstitution.institution_id == institution_id
        ).subquery()
        # Include by group membership OR by orientador being in the institution
        q = q.filter(
            or_(
                Researcher.group_id.in_(group_ids),
                Researcher.orientador_id.in_(prof_ids),
            )
        )
    results = q.order_by(Researcher.nome).all()
    # Superadmin users are invisible to all profiles
    return [r for r in results if not (r.user and r.user.role == 'superadmin')]


def create(db: Session, data: ResearcherCreate) -> Researcher:
    payload = data.model_dump()
    # Auto-resolve group_id from orientador if not explicitly provided
    if payload.get("group_id") is None and payload.get("orientador_id") is not None:
        payload["group_id"] = _resolve_group_id(db, payload["orientador_id"])
    researcher = Researcher(**payload)
    db.add(researcher)
    db.commit()
    db.refresh(researcher)
    logger.info("Researcher created: %s (id=%s)", researcher.nome, researcher.id)
    return researcher


def get_by_id(db: Session, researcher_id: int) -> Researcher | None:
    return db.query(Researcher).get(researcher_id)


def find_by_slug(db: Session, slug: str) -> Researcher | None:
    researchers = db.query(Researcher).filter(Researcher.ativo == True).all()
    for r in researchers:
        if slugify(r.nome) == slug:
            return r
    return None


def get_linked_user(db: Session, researcher_id: int) -> User | None:
    return db.query(User).filter(User.researcher_id == researcher_id).first()


def update(db: Session, researcher: Researcher, data: ResearcherUpdate) -> Researcher:
    payload = data.model_dump(exclude_unset=True)

    # When orientador changes, auto-update group_id (unless explicitly provided)
    if "orientador_id" in payload and "group_id" not in payload:
        payload["group_id"] = _resolve_group_id(db, payload["orientador_id"])

    for key, value in payload.items():
        setattr(researcher, key, value)
    db.commit()
    db.refresh(researcher)
    logger.info("Researcher updated: id=%s", researcher.id)
    return researcher


def deactivate(db: Session, researcher: Researcher) -> None:
    researcher.ativo = False
    db.commit()
    logger.info("Researcher deactivated: id=%s", researcher.id)

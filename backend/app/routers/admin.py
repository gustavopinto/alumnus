from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import and_, func, or_
from sqlalchemy.orm import Session, joinedload

from ..database import get_db
from ..deps import require_dashboard, require_superadmin, require_professor
from ..models import User, Researcher, Reminder, Tip, TipComment, Note, ResearchGroup, ProfessorGroup, Professor, ProfessorInstitution
from ..services import professor_service
from ..plan import clear_plan, ensure_professor_plan_defaults

router = APIRouter(prefix="/admin", tags=["admin"])

VALID_ROLES = ("professor", "student", "superadmin")

_ADMIN_USER_LIST_ROLE_ORDER = {
    "superadmin": 0,
    "professor":  1,
    "student":    2,
}


class UserRoleUpdate(BaseModel):
    role: str


class BulkDeleteRequest(BaseModel):
    user_ids: list[int] = []
    researcher_ids: list[int] = []


def _is_superadmin(user: User) -> bool:
    return user.role == "superadmin"


def _count_groups(db: Session, current: User | None) -> int:
    """Superadmin vê todos os grupos; professor vê apenas seus grupos."""
    if current is None or _is_superadmin(current):
        return db.query(func.count(ResearchGroup.id)).scalar()
    professor = professor_service.get_by_user(db, current)
    if not professor:
        return 0
    return db.query(func.count(ProfessorGroup.group_id)).filter(
        ProfessorGroup.professor_id == professor.id
    ).scalar()


def _stats_global(db: Session, hide_superadmin_count: bool, current: User = None) -> dict:
    """Estatísticas globais; se hide_superadmin_count, não expõe quantidade de superadmins."""
    if hide_superadmin_count:
        role_counts = (
            db.query(User.role, func.count(User.id))
            .filter(User.role != "superadmin")
            .group_by(User.role)
            .all()
        )
        by_role = {role: cnt for role, cnt in role_counts}
        users_by_role = {
            "superadmin": 0,
            "professor":  by_role.get("professor", 0),
            "student":    by_role.get("student", 0),
        }
    else:
        role_counts = db.query(User.role, func.count(User.id)).group_by(User.role).all()
        by_role = {role: cnt for role, cnt in role_counts}
        users_by_role = {
            "superadmin": by_role.get("superadmin", 0),
            "professor":  by_role.get("professor", 0),
            "student":    by_role.get("student", 0),
        }

    researchers, pending = db.query(
        func.count(Researcher.id).filter(Researcher.ativo.is_(True)),
        func.count(Researcher.id).filter(Researcher.ativo.is_(True), Researcher.registered.is_(False)),
    ).one()

    return {
        "users_by_role":        users_by_role,
        "total_researchers":    researchers,
        "total_pending":        pending,
        "total_groups":         _count_groups(db, current),
        "total_reminders":      db.query(func.count(Reminder.id)).scalar(),
        "total_tips":           db.query(func.count(Tip.id)).scalar(),
        "total_notes":          db.query(func.count(Note.id)).scalar(),
    }


# ── Stats ─────────────────────────────────────────────────────────────────────

@router.get("/stats")
def get_stats(db: Session = Depends(get_db), current: User = Depends(require_dashboard)):
    # Superadmin: tudo. Professor/admin: totais globais, mas sem revelar quantos superadmins existem.
    return _stats_global(db, hide_superadmin_count=not _is_superadmin(current), current=current)


# ── Users list ────────────────────────────────────────────────────────────────

@router.get("/users")
def list_users(db: Session = Depends(get_db), current: User = Depends(require_dashboard)):
    def _institutions_for_user(u: User) -> list:
        if u.professor:
            return [pi.institution.name for pi in u.professor.professor_institutions if pi.institution]
        if u.researcher and u.researcher.group and u.researcher.group.institution:
            return [u.researcher.group.institution.name]
        return []

    def _institutions_for_pending(r: Researcher) -> list:
        if r.group and r.group.institution:
            return [r.group.institution.name]
        return []

    def _serialize_user(u: User) -> dict:
        return {
            "id": u.id,
            "email": u.email,
            "nome": u.nome,
            "role": u.role,
            "is_admin": u.is_admin,
            "researcher_id": u.researcher_id,
            "researcher_nome": u.researcher.nome if u.researcher else None,
            "researcher_status": u.researcher.status if u.researcher else None,
            "whatsapp": u.whatsapp,
            "photo_url": u.photo_thumb_url or u.photo_url,
            "last_login": u.last_login,
            "created_at": u.created_at,
            "pending": False,
            "institutions": _institutions_for_user(u),
        }

    def _serialize_pending(r: Researcher) -> dict:
        return {
            "id": None,
            "email": r.email or "—",
            "nome": r.nome,
            "role": "student",
            "researcher_id": r.id,
            "researcher_nome": r.nome,
            "researcher_status": r.status,
            "last_login": None,
            "created_at": None,
            "whatsapp": None,
            "photo_url": None,
            "pending": True,
            "institutions": _institutions_for_pending(r),
        }

    eager_opts = [
        joinedload(User.researcher).joinedload(Researcher.group).joinedload(ResearchGroup.institution),
        joinedload(User.professor).joinedload(Professor.professor_institutions).joinedload(ProfessorInstitution.institution),
    ]

    if _is_superadmin(current):
        users = (
            db.query(User)
            .options(*eager_opts)
            .all()
        )
    else:
        # Professor/admin: todos, exceto superadmin "puro" (sem perfil de pesquisador).
        # Orientadores costumam estar como superadmin após migrações; com researcher_id entram na lista.
        users = (
            db.query(User)
            .options(*eager_opts)
            .filter(
                or_(
                    User.role != "superadmin",
                    and_(User.role == "superadmin", User.researcher_id.isnot(None)),
                )
            )
            .all()
        )

    pending = (
        db.query(Researcher)
        .options(joinedload(Researcher.group).joinedload(ResearchGroup.institution))
        .filter(
            Researcher.ativo.is_(True),
            Researcher.registered.is_(False),
        )
        .all()
    )

    def _user_sort_key(u: User) -> tuple:
        role_rank = _ADMIN_USER_LIST_ROLE_ORDER.get(u.role, 99)
        return (role_rank, (u.nome or "").strip().lower())

    users_sorted = sorted(users, key=_user_sort_key)
    pending_sorted = sorted(pending, key=lambda r: (r.nome or "").strip().lower())

    return [_serialize_user(u) for u in users_sorted] + [_serialize_pending(r) for r in pending_sorted]


# ── Role update (superadmin only) ─────────────────────────────────────────────

@router.put("/users/{user_id}")
def update_user(
    user_id: int,
    data: UserRoleUpdate,
    db: Session = Depends(get_db),
    current: User = Depends(require_superadmin),
):
    if user_id == current.id:
        raise HTTPException(status_code=400, detail="Você não pode alterar o próprio perfil")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    if data.role not in VALID_ROLES:
        raise HTTPException(status_code=400, detail="Perfil inválido")

    old_role = user.role
    user.role = data.role
    user.is_admin = data.role == "superadmin"

    if data.role == "student":
        clear_plan(user)
    elif data.role in ("professor", "superadmin") and old_role not in ("professor", "superadmin"):
        ensure_professor_plan_defaults(user)

    db.commit()
    return {"id": user.id, "role": user.role, "is_admin": user.is_admin}


# ── Delete user (superadmin only) ─────────────────────────────────────────────

@router.delete("/users/{user_id}", status_code=204)
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current: User = Depends(require_dashboard),
):
    if user_id == current.id:
        raise HTTPException(status_code=400, detail="Você não pode remover a própria conta")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    if user.role == "superadmin" and current.role != "superadmin":
        raise HTTPException(status_code=403, detail="Apenas superadmin pode remover outro superadmin")
    if user.researcher_id:
        researcher = db.query(Researcher).filter(Researcher.id == user.researcher_id).first()
        if researcher:
            researcher.ativo = False
            researcher.registered = False
    # Nullify FK references to avoid integrity errors
    db.query(Note).filter(Note.created_by_id == user_id).update({"created_by_id": None})
    db.query(Reminder).filter(Reminder.created_by_id == user_id).update({"created_by_id": None})
    db.query(Tip).filter(Tip.author_id == user_id).update({"author_id": None})
    db.query(TipComment).filter(TipComment.author_id == user_id).update({"author_id": None})
    db.delete(user)
    db.commit()


# ── Bulk delete (superadmin only) ─────────────────────────────────────────────

@router.post("/bulk-delete", status_code=204)
def bulk_delete(
    data: BulkDeleteRequest,
    db: Session = Depends(get_db),
    current: User = Depends(require_dashboard),
):
    for uid in data.user_ids:
        if uid == current.id:
            continue
        user = db.query(User).filter(User.id == uid).first()
        if user and not (user.role == "superadmin" and current.role != "superadmin"):
            if user.researcher_id:
                researcher = db.query(Researcher).filter(Researcher.id == user.researcher_id).first()
                if researcher:
                    researcher.ativo = False
                    researcher.registered = False
            db.query(Note).filter(Note.created_by_id == uid).update({"created_by_id": None})
            db.query(Reminder).filter(Reminder.created_by_id == uid).update({"created_by_id": None})
            db.query(Tip).filter(Tip.author_id == uid).update({"author_id": None})
            db.query(TipComment).filter(TipComment.author_id == uid).update({"author_id": None})
            db.delete(user)
    for rid in data.researcher_ids:
        researcher = db.query(Researcher).filter(Researcher.id == rid).first()
        if researcher and not researcher.registered:
            db.delete(researcher)
    db.commit()


# ── Delete pending researcher (superadmin only) ────────────────────────────────

@router.delete("/researchers/{researcher_id}", status_code=204)
def delete_pending_researcher(
    researcher_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_dashboard),
):
    researcher = db.query(Researcher).filter(Researcher.id == researcher_id).first()
    if not researcher:
        raise HTTPException(status_code=404, detail="Pesquisador não encontrado")
    if researcher.registered:
        raise HTTPException(status_code=400, detail="Pesquisador já possui conta — remova o usuário")
    db.delete(researcher)
    db.commit()

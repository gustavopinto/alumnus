from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import func, case
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import require_admin
from ..models import User, Researcher, Reminder, BoardPost, ManualEntry, Note
from ..plan import clear_plan, ensure_professor_plan_defaults

router = APIRouter(prefix="/admin", tags=["admin"])


class UserRoleUpdate(BaseModel):
    role: str
    is_admin: bool = False


@router.get("/stats")
def get_stats(db: Session = Depends(get_db), _: User = Depends(require_admin)):
    role_counts = db.query(User.role, func.count(User.id)).group_by(User.role).all()
    by_role = {role: cnt for role, cnt in role_counts}
    by_role["admin"] = db.query(func.count(User.id)).filter(User.is_admin.is_(True)).scalar()

    researchers, pending = db.query(
        func.count(Researcher.id).filter(Researcher.ativo.is_(True)),
        func.count(Researcher.id).filter(Researcher.ativo.is_(True), Researcher.registered.is_(False)),
    ).one()

    return {
        "users_by_role": {
            "admin":     by_role.get("admin", 0),
            "professor": by_role.get("professor", 0),
            "student":   by_role.get("student", 0),
        },
        "total_researchers":    researchers,
        "total_pending":        pending,
        "total_reminders":      db.query(func.count(Reminder.id)).scalar(),
        "total_board_posts":    db.query(func.count(BoardPost.id)).scalar(),
        "total_manual_entries": db.query(func.count(ManualEntry.id)).scalar(),
        "total_notes":          db.query(func.count(Note.id)).scalar(),
    }


@router.get("/users")
def list_users(db: Session = Depends(get_db), _: User = Depends(require_admin)):
    users = db.query(User).order_by(User.role, User.nome).all()

    pending = db.query(Researcher).filter(
        Researcher.ativo.is_(True),
        Researcher.registered.is_(False),
    ).order_by(Researcher.nome).all()

    result = [
        {
            "id": u.id,
            "email": u.email,
            "nome": u.nome,
            "role": u.role,
            "is_admin": u.is_admin,
            "researcher_id": u.researcher_id,
            "researcher_nome": u.researcher.nome if u.researcher else None,
            "whatsapp": u.researcher.whatsapp if u.researcher else None,
            "photo_url": (u.researcher.photo_thumb_url or u.researcher.photo_url) if u.researcher else None,
            "last_login": u.last_login,
            "created_at": u.created_at,
            "pending": False,
        }
        for u in users
    ]

    result += [
        {
            "id": None,
            "email": r.email or "—",
            "nome": r.nome,
            "role": "student",
            "researcher_id": r.id,
            "researcher_nome": r.nome,
            "last_login": None,
            "created_at": None,
            "whatsapp": r.whatsapp,
            "photo_url": r.photo_thumb_url or r.photo_url,
            "pending": True,
        }
        for r in pending
    ]

    return result


@router.put("/users/{user_id}")
def update_user(
    user_id: int,
    data: UserRoleUpdate,
    db: Session = Depends(get_db),
    current: User = Depends(require_admin),
):
    if user_id == current.id:
        raise HTTPException(status_code=400, detail="Você não pode alterar o próprio perfil")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    if data.role not in ("admin", "professor", "student"):
        raise HTTPException(status_code=400, detail="Perfil inválido")
    old_role = user.role
    user.role = data.role
    user.is_admin = data.is_admin
    if data.role != "professor":
        clear_plan(user)
    elif old_role != "professor":
        ensure_professor_plan_defaults(user)
    db.commit()
    return {"id": user.id, "role": user.role, "is_admin": user.is_admin}


@router.delete("/users/{user_id}", status_code=204)
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current: User = Depends(require_admin),
):
    if user_id == current.id:
        raise HTTPException(status_code=400, detail="Você não pode remover a própria conta")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    db.delete(user)
    db.commit()


@router.delete("/researchers/{researcher_id}", status_code=204)
def delete_pending_researcher(
    researcher_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    researcher = db.query(Researcher).filter(Researcher.id == researcher_id).first()
    if not researcher:
        raise HTTPException(status_code=404, detail="Pesquisador não encontrado")
    if researcher.registered:
        raise HTTPException(status_code=400, detail="Pesquisador já possui conta — remova o usuário")
    db.delete(researcher)
    db.commit()

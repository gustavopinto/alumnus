from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import require_admin
from ..models import User, Researcher, Reminder, BoardPost, ManualEntry, Note

router = APIRouter(prefix="/admin", tags=["admin"])


class UserRoleUpdate(BaseModel):
    role: str


@router.get("/stats")
def get_stats(db: Session = Depends(get_db), _: User = Depends(require_admin)):
    users = db.query(User).all()
    by_role: dict[str, int] = {}
    for u in users:
        by_role[u.role] = by_role.get(u.role, 0) + 1

    return {
        "users_by_role": by_role,
        "total_researchers": db.query(Researcher).filter(Researcher.ativo == True).count(),
        "total_reminders": db.query(Reminder).count(),
        "total_board_posts": db.query(BoardPost).count(),
        "total_manual_entries": db.query(ManualEntry).count(),
        "total_notes": db.query(Note).count(),
    }


@router.get("/users")
def list_users(db: Session = Depends(get_db), _: User = Depends(require_admin)):
    users = db.query(User).order_by(User.role, User.nome).all()
    return [
        {
            "id": u.id,
            "email": u.email,
            "nome": u.nome,
            "role": u.role,
            "researcher_id": u.researcher_id,
            "researcher_nome": u.researcher.nome if u.researcher else None,
            "last_login": u.last_login,
            "created_at": u.created_at,
        }
        for u in users
    ]


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
    user.role = data.role
    db.commit()
    return {"id": user.id, "role": user.role}


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

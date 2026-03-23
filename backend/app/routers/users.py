from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_current_user, require_dashboard
from ..models import User
from ..schemas import UserProfileUpdate, UserOut
from ..plan import user_to_out, refresh_user_plan_status
from ..services import user_service

router = APIRouter(prefix="/users", tags=["users"])


@router.patch("/me", response_model=UserOut)
def update_my_profile(
    data: UserProfileUpdate,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
):
    user_service.update_profile(db, current, data.model_dump(exclude_unset=True))
    db.refresh(current)
    refresh_user_plan_status(db, current)
    return user_to_out(current)


@router.patch("/{user_id}", response_model=UserOut)
def update_user_profile(
    user_id: int,
    data: UserProfileUpdate,
    db: Session = Depends(get_db),
    current: User = Depends(require_dashboard),
):
    """Professor ou superadmin pode editar o perfil de qualquer usuário."""
    user = user_service.get_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    # Student can only edit own profile
    if current.role == "student" and current.id != user_id:
        raise HTTPException(status_code=403, detail="Sem permissão")
    user_service.update_profile(db, user, data.model_dump(exclude_unset=True))
    db.refresh(user)
    return user_to_out(user)

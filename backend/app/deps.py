import os
from typing import Optional

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from .database import get_db
from .models import User
from .services import user_service

SECRET_KEY = os.getenv("SECRET_KEY", "alumnus_dev_secret_troque_em_producao")
ALGORITHM = "HS256"
bearer = HTTPBearer()
optional_bearer = HTTPBearer(auto_error=False)

# Papéis com acesso ao dashboard (filtrado pelo próprio grupo, exceto superadmin)
DASHBOARD_ROLES = {"professor", "admin", "superadmin"}


def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        raise HTTPException(status_code=401, detail="Token inválido ou expirado")


def get_current_user(
    creds: HTTPAuthorizationCredentials = Depends(bearer),
    db: Session = Depends(get_db),
) -> User:
    payload = decode_token(creds.credentials)
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Token mal formado")
    user = user_service.get_by_id(db, int(user_id))
    if not user:
        raise HTTPException(status_code=401, detail="Usuário não encontrado")
    return user


def get_optional_user(
    creds: Optional[HTTPAuthorizationCredentials] = Depends(optional_bearer),
    db: Session = Depends(get_db),
) -> Optional[User]:
    if not creds:
        return None
    try:
        payload = decode_token(creds.credentials)
        user_id = payload.get("sub")
        if not user_id:
            return None
        return user_service.get_by_id(db, int(user_id))
    except Exception:
        return None


def require_professor(user: User = Depends(get_current_user)) -> User:
    """Professor, admin ou superadmin."""
    if user.role not in DASHBOARD_ROLES:
        raise HTTPException(status_code=403, detail="Acesso restrito a professores")
    return user


def require_dashboard(user: User = Depends(get_current_user)) -> User:
    """Acesso ao dashboard: professor, admin e superadmin."""
    if user.role not in DASHBOARD_ROLES:
        raise HTTPException(status_code=403, detail="Acesso restrito ao dashboard")
    return user


def require_superadmin(user: User = Depends(get_current_user)) -> User:
    """Acesso total: apenas superadmin."""
    if user.role != "superadmin":
        raise HTTPException(status_code=403, detail="Acesso restrito a superadmin")
    return user


# Mantido por compatibilidade — equivalente a require_dashboard
def require_admin(user: User = Depends(get_current_user)) -> User:
    if user.role not in DASHBOARD_ROLES:
        raise HTTPException(status_code=403, detail="Acesso restrito a administradores")
    return user


def is_privileged(user: User) -> bool:
    """Retorna True para professor, admin e superadmin."""
    return user.role in DASHBOARD_ROLES

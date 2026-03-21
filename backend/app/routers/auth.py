import os
import logging
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from passlib.context import CryptContext
from jose import jwt
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import User
from ..schemas import RegisterRequest, LoginRequest, TokenOut, UserOut
from ..deps import get_current_user, SECRET_KEY, ALGORITHM
from ..services import auth_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["auth"])
pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")
EXPIRE_H = int(os.getenv("TOKEN_EXPIRE_HOURS", "8"))


def make_token(user: User) -> str:
    payload = {
        "sub": str(user.id),
        "role": user.role,
        "researcher_id": user.researcher_id,
        "exp": datetime.utcnow() + timedelta(hours=EXPIRE_H),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


@router.post("/register", response_model=UserOut, status_code=201)
def register(data: RegisterRequest, db: Session = Depends(get_db)):
    if auth_service.user_email_exists(db, data.email):
        raise HTTPException(status_code=409, detail="Email já cadastrado")

    researcher = auth_service.get_active_researcher_for_email(db, data.email)
    if not researcher:
        raise HTTPException(
            status_code=404,
            detail="Email não encontrado. Entre em contato com seu orientador.",
        )

    user = auth_service.create_student_from_researcher(db, data, researcher, pwd_ctx)
    return user


@router.post("/login", response_model=TokenOut)
def login(data: LoginRequest, db: Session = Depends(get_db)):
    user = auth_service.authenticate(db, data.email, data.password, pwd_ctx)
    if not user:
        raise HTTPException(status_code=401, detail="Credenciais inválidas")
    auth_service.record_login(db, user)
    return TokenOut(access_token=make_token(user))


@router.get("/me", response_model=UserOut)
def me(current: User = Depends(get_current_user)):
    return current

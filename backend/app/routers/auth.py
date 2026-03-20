import os
import logging
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from passlib.context import CryptContext
from jose import jwt
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import User, Student
from ..schemas import RegisterRequest, LoginRequest, TokenOut, UserOut
from ..deps import get_current_user, SECRET_KEY, ALGORITHM

logger   = logging.getLogger(__name__)
router   = APIRouter(prefix="/auth", tags=["auth"])
pwd_ctx  = CryptContext(schemes=["bcrypt"], deprecated="auto")
EXPIRE_H = int(os.getenv("TOKEN_EXPIRE_HOURS", "8"))


def make_token(user: User) -> str:
    payload = {
        "sub":        str(user.id),
        "role":       user.role,
        "student_id": user.student_id,
        "exp":        datetime.utcnow() + timedelta(hours=EXPIRE_H),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


@router.post("/register", response_model=UserOut, status_code=201)
def register(data: RegisterRequest, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == data.email).first():
        raise HTTPException(status_code=409, detail="Email já cadastrado")

    student = db.query(Student).filter(
        Student.email == data.email,
        Student.ativo == True,
    ).first()

    if not student:
        raise HTTPException(
            status_code=404,
            detail="Email não encontrado. Entre em contato com seu orientador."
        )

    user = User(
        email=data.email,
        nome=student.nome,
        password_hash=pwd_ctx.hash(data.password),
        role="student",
        student_id=student.id,
    )
    db.add(user)
    student.registered = True
    db.commit()
    db.refresh(user)
    logger.info("User registered: %s (student)", user.email)
    return user


@router.post("/login", response_model=TokenOut)
def login(data: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == data.email).first()
    if not user or not pwd_ctx.verify(data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Credenciais inválidas")
    return TokenOut(access_token=make_token(user))


@router.get("/me", response_model=UserOut)
def me(current: User = Depends(get_current_user)):
    return current

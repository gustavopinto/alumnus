import logging
from datetime import datetime

from passlib.context import CryptContext
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..models import Researcher, User
from ..schemas import RegisterRequest

logger = logging.getLogger(__name__)


def _norm_email(email: str) -> str:
    return (email or "").strip().lower()


def user_email_exists(db: Session, email: str) -> bool:
    e = _norm_email(email)
    return (
        db.query(User).filter(func.lower(User.email) == e).first() is not None
    )


def get_active_researcher_for_email(db: Session, email: str) -> Researcher | None:
    e = _norm_email(email)
    return (
        db.query(Researcher)
        .filter(func.lower(Researcher.email) == e, Researcher.ativo == True)
        .first()
    )


def create_student_from_researcher(
    db: Session,
    data: RegisterRequest,
    researcher: Researcher,
    pwd_ctx: CryptContext,
) -> User:
    user = User(
        email=data.email,
        nome=researcher.nome,
        password_hash=pwd_ctx.hash(data.password),
        role="student",
        researcher_id=researcher.id,
    )
    db.add(user)
    researcher.registered = True
    db.commit()
    db.refresh(user)
    logger.info("User registered: %s (student)", user.email)
    return user


def authenticate(
    db: Session, email: str, password: str, pwd_ctx: CryptContext
) -> User | None:
    e = _norm_email(email)
    user = db.query(User).filter(func.lower(User.email) == e).first()
    if not user or not pwd_ctx.verify(password, user.password_hash):
        return None
    return user


def record_login(db: Session, user: User) -> None:
    user.last_login = datetime.utcnow()
    db.commit()

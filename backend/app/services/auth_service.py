import logging
from datetime import datetime

from passlib.context import CryptContext
from sqlalchemy.orm import Session

from ..models import Researcher, User
from ..schemas import RegisterRequest

logger = logging.getLogger(__name__)


def user_email_exists(db: Session, email: str) -> bool:
    return db.query(User).filter(User.email == email).first() is not None


def get_active_researcher_for_email(db: Session, email: str) -> Researcher | None:
    return (
        db.query(Researcher)
        .filter(Researcher.email == email, Researcher.ativo == True)
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
    user = db.query(User).filter(User.email == email).first()
    if not user or not pwd_ctx.verify(password, user.password_hash):
        return None
    return user


def record_login(db: Session, user: User) -> None:
    user.last_login = datetime.utcnow()
    db.commit()

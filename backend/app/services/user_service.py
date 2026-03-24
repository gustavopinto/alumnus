from passlib.context import CryptContext
from sqlalchemy.orm import Session

from ..models import User

_pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_by_id(db: Session, user_id: int) -> User | None:
    return db.query(User).get(user_id)


def update_profile(db: Session, user: User, data: dict) -> User:
    for key, value in data.items():
        if key == "password":
            if value:
                user.password_hash = _pwd_ctx.hash(value)
        elif hasattr(user, key):
            setattr(user, key, value)
    db.commit()
    db.refresh(user)
    return user

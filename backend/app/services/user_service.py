from sqlalchemy.orm import Session

from ..models import User


def get_by_id(db: Session, user_id: int) -> User | None:
    return db.query(User).get(user_id)

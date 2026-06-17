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


def user_to_out(user: User) -> "UserOut":
    from ..schemas import UserOut
    inst_id, inst_name = None, None
    if user.researcher_id and user.researcher:
        r = user.researcher
        if r.group_id and r.group:
            g = r.group
            if g.institution:
                inst_id = g.institution.id
                inst_name = g.institution.name
            else:
                inst_id = g.institution_id
    return UserOut(
        id=user.id,
        email=user.email,
        nome=user.nome,
        role=user.role,
        professor_id=user.professor_id,
        researcher_id=user.researcher_id,
        last_login=user.last_login,
        created_at=user.created_at,
        photo_url=user.photo_url,
        photo_thumb_url=user.photo_thumb_url,
        lattes_url=user.lattes_url,
        scholar_url=user.scholar_url,
        linkedin_url=user.linkedin_url,
        github_url=user.github_url,
        instagram_url=user.instagram_url,
        twitter_url=user.twitter_url,
        whatsapp=user.whatsapp,
        interesses=user.interesses,
        bio=user.bio,
        birth_date=user.birth_date,
        institution_id=inst_id,
        institution_name=inst_name,
    )

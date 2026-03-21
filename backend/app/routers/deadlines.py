from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session, joinedload

from ..database import get_db
from ..models import DeadlineInterest, Researcher
from ..schemas import DeadlineInterestOut
from ..deps import get_current_user
from ..models import User
from ..slug import slugify

router = APIRouter(prefix="/deadlines", tags=["deadlines"])


def _to_out(db: Session, interest: DeadlineInterest) -> DeadlineInterestOut:
    photo = None
    profile_slug = None
    u = interest.user
    if not u:
        return DeadlineInterestOut(
            deadline_key=interest.deadline_key,
            user_id=interest.user_id,
            user_name="",
            user_photo_url=None,
            profile_slug=None,
        )
    if u.researcher:
        photo = u.researcher.photo_url
        profile_slug = slugify(u.researcher.nome)
    elif u.researcher_id is not None:
        r = db.query(Researcher).filter(Researcher.id == u.researcher_id).first()
        if r:
            photo = r.photo_url
            profile_slug = slugify(r.nome)
    if profile_slug is None and u.nome:
        profile_slug = slugify(u.nome)
    return DeadlineInterestOut(
        deadline_key=interest.deadline_key,
        user_id=interest.user_id,
        user_name=u.nome,
        user_photo_url=photo,
        profile_slug=profile_slug,
    )


@router.get("/interests", response_model=list[DeadlineInterestOut])
def list_interests(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    interests = (
        db.query(DeadlineInterest)
        .options(joinedload(DeadlineInterest.user).joinedload(User.researcher))
        .all()
    )
    return [_to_out(db, i) for i in interests]


@router.post("/{key:path}/interest", status_code=204)
def toggle_interest(
    key: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    existing = db.query(DeadlineInterest).filter_by(deadline_key=key, user_id=current_user.id).first()
    if existing:
        db.delete(existing)
    else:
        db.add(DeadlineInterest(deadline_key=key, user_id=current_user.id))
    db.commit()
    return Response(status_code=204)

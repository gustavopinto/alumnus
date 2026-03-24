from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_current_user
from ..models import User
from ..schemas import ProfileBySlugOut, ResearcherOut
from ..slug import slugify
from ..plan import refresh_user_plan_status, user_to_out
from ..services import researcher_service

router = APIRouter(prefix="/profiles", tags=["profiles"])


@router.get("/by-slug/{slug}", response_model=ProfileBySlugOut)
def get_profile_by_slug(
    slug: str,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    users = db.query(User).all()
    for user in users:
        if slugify(user.nome) != slug:
            continue
        refresh_user_plan_status(db, user)
        db.refresh(user)
        researcher_out = None
        if user.researcher_id:
            researcher = researcher_service.get_by_id(db, user.researcher_id)
            if researcher:
                researcher_out = ResearcherOut.model_validate(researcher)
        return ProfileBySlugOut(user=user_to_out(user), researcher=researcher_out)

    researcher = researcher_service.find_by_slug(db, slug)
    if not researcher:
        raise HTTPException(status_code=404, detail="Perfil não encontrado")
    linked_user = researcher_service.get_linked_user(db, researcher.id)
    user_out = None
    if linked_user:
        refresh_user_plan_status(db, linked_user)
        db.refresh(linked_user)
        user_out = user_to_out(linked_user)
    return ProfileBySlugOut(user=user_out, researcher=ResearcherOut.model_validate(researcher))

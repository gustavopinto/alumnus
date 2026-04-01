from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, contains_eager

from ..database import get_db
from ..deps import get_current_user
from ..models import Researcher, User
from ..schemas import ProfileBySlugOut, ResearcherOut
from ..slug import slugify
from ..plan import refresh_user_plan_status, user_to_out

router = APIRouter(prefix="/profiles", tags=["profiles"])


@router.get("/by-slug/{slug}", response_model=ProfileBySlugOut)
def get_profile_by_slug(
    slug: str,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    # Tenta achar pelo lado do Researcher (users com researcher_id)
    # contains_eager(Researcher.user) garante que .nome/.email/.registered funcionam sem lazy load
    researchers = (
        db.query(Researcher)
        .outerjoin(User, User.researcher_id == Researcher.id)
        .options(contains_eager(Researcher.user))
        .filter(User.ativo == True)
        .all()
    )
    researcher = next((r for r in researchers if r.user and slugify(r.user.nome) == slug), None)
    if researcher:
        user = researcher.user
        refresh_user_plan_status(db, user)
        db.refresh(user)
        return ProfileBySlugOut(user=user_to_out(user), researcher=ResearcherOut.model_validate(researcher))

    # Fallback: professores / superadmins (sem researcher_id)
    users = (
        db.query(User)
        .filter(User.ativo == True, User.researcher_id.is_(None))
        .all()
    )
    user = next((u for u in users if slugify(u.nome) == slug), None)
    if not user:
        raise HTTPException(status_code=404, detail="Perfil não encontrado")
    refresh_user_plan_status(db, user)
    db.refresh(user)
    return ProfileBySlugOut(user=user_to_out(user), researcher=None)

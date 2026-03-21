import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import BoardPost, User
from ..schemas import BoardPostCreate, BoardPostOut
from ..deps import decode_token

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/board", tags=["board"])
bearer = HTTPBearer(auto_error=False)


def _get_optional_user(
    creds: Optional[HTTPAuthorizationCredentials] = Depends(bearer),
    db: Session = Depends(get_db),
) -> Optional[User]:
    if not creds:
        return None
    try:
        payload = decode_token(creds.credentials)
        user_id = payload.get("sub")
        return db.query(User).get(int(user_id)) if user_id else None
    except Exception:
        return None


@router.get("/", response_model=list[BoardPostOut])
def list_posts(db: Session = Depends(get_db)):
    posts = db.query(BoardPost).order_by(BoardPost.created_at.desc()).all()
    return [BoardPostOut.from_orm_with_author(p) for p in posts]


@router.post("/", response_model=BoardPostOut, status_code=201)
def create_post(
    data: BoardPostCreate,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(_get_optional_user),
):
    post = BoardPost(
        text=data.text,
        author_id=current_user.id if current_user else None,
    )
    db.add(post)
    db.commit()
    db.refresh(post)
    logger.info("Board post created by user %s", current_user.id if current_user else "anonymous")
    return BoardPostOut.from_orm_with_author(post)


@router.delete("/{post_id}", status_code=204)
def delete_post(
    post_id: int,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(_get_optional_user),
):
    post = db.query(BoardPost).get(post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    if not current_user:
        raise HTTPException(status_code=401, detail="Authentication required")
    is_professor = current_user.role == "professor"
    is_author = post.author_id == current_user.id
    if not is_professor and not is_author:
        raise HTTPException(status_code=403, detail="Not allowed")
    db.delete(post)
    db.commit()
    logger.info("Board post deleted: id=%s", post_id)

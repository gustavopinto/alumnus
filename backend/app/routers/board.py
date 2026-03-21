import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import User
from ..schemas import BoardPostCreate, BoardPostOut
from ..deps import get_optional_user
from ..services import board_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/board", tags=["board"])


@router.get("/", response_model=list[BoardPostOut])
def list_posts(db: Session = Depends(get_db)):
    posts = board_service.list_posts(db)
    return [BoardPostOut.from_orm_with_author(p) for p in posts]


@router.post("/", response_model=BoardPostOut, status_code=201)
def create_post(
    data: BoardPostCreate,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user),
):
    author_id = current_user.id if current_user else None
    post = board_service.create_post(db, data.text, author_id)
    return BoardPostOut.from_orm_with_author(post)


@router.delete("/{post_id}", status_code=204)
def delete_post(
    post_id: int,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user),
):
    post = board_service.get_post(db, post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    if not current_user:
        raise HTTPException(status_code=401, detail="Authentication required")
    is_professor = current_user.role in ("professor", "admin")
    is_author = post.author_id == current_user.id
    if not is_professor and not is_author:
        raise HTTPException(status_code=403, detail="Not allowed")
    board_service.delete_post(db, post)

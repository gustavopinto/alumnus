import logging
from typing import Optional

from sqlalchemy.orm import Session

from ..models import BoardPost

logger = logging.getLogger(__name__)


def list_posts(db: Session) -> list[BoardPost]:
    return db.query(BoardPost).order_by(BoardPost.created_at.desc()).all()


def create_post(db: Session, text: str, author_id: Optional[int]) -> BoardPost:
    post = BoardPost(text=text, author_id=author_id)
    db.add(post)
    db.commit()
    db.refresh(post)
    logger.info(
        "Board post created by user %s",
        author_id if author_id is not None else "anonymous",
    )
    return post


def get_post(db: Session, post_id: int) -> BoardPost | None:
    return db.query(BoardPost).get(post_id)


def delete_post(db: Session, post: BoardPost) -> None:
    db.delete(post)
    db.commit()
    logger.info("Board post deleted: id=%s", post.id)

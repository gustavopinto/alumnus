from sqlalchemy.orm import Session

from ..models import FileUpload


def get_upload(db: Session, file_id: int) -> FileUpload | None:
    return db.query(FileUpload).get(file_id)

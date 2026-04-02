import logging

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import SessionLocal, get_db
from ..deps import get_current_user
from ..models import User
from ..schemas import ReadingCreate, ReadingOut, ReadingStatusUpdate
from ..services import reading_service
from ..services.user_service import get_by_id as get_user_by_id

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/users/{user_id}/readings", tags=["readings"])


def _get_user_or_404(user_id: int, db: Session) -> User:
    u = get_user_by_id(db, user_id)
    if not u:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    return u


def _check_can_edit(current_user: User, user_id: int):
    is_own = current_user.id == user_id
    if current_user.role not in ("professor", "superadmin") and not is_own:
        raise HTTPException(status_code=403, detail="Sem permissão para editar leituras deste usuário")


def _get_reading_or_404(reading_id: int, user_id: int, db: Session):
    reading = reading_service.get_by_id(db, reading_id)
    if not reading or reading.user_id != user_id:
        raise HTTPException(status_code=404, detail="Leitura não encontrada")
    return reading


@router.get("/", response_model=list[ReadingOut])
def list_readings(
    user_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    _get_user_or_404(user_id, db)
    readings = reading_service.list_by_user(db, user_id)
    return [ReadingOut.from_orm_with_history(r) for r in readings]


@router.post("/", response_model=ReadingOut, status_code=201)
def create_reading(
    user_id: int,
    data: ReadingCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _get_user_or_404(user_id, db)
    _check_can_edit(current_user, user_id)
    if reading_service.exists(db, user_id, data.url):
        raise HTTPException(status_code=409, detail="Este paper já foi adicionado para este usuário.")
    reading = reading_service.create(db, user_id, data.url, current_user.id)
    background_tasks.add_task(
        reading_service.fetch_and_set_title,
        reading.id,
        data.url,
        SessionLocal,
    )
    return ReadingOut.from_orm_with_history(reading)


@router.patch("/{reading_id}", response_model=ReadingOut)
def update_reading_status(
    user_id: int,
    reading_id: int,
    data: ReadingStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _get_user_or_404(user_id, db)
    _check_can_edit(current_user, user_id)
    reading = _get_reading_or_404(reading_id, user_id, db)
    reading = reading_service.update_status(db, reading, data.status, current_user.id)
    return ReadingOut.from_orm_with_history(reading)


@router.post("/{reading_id}/summarize", response_model=ReadingOut)
def summarize_reading(
    user_id: int,
    reading_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _get_user_or_404(user_id, db)
    _check_can_edit(current_user, user_id)
    reading = _get_reading_or_404(reading_id, user_id, db)
    background_tasks.add_task(
        reading_service.generate_summary,
        reading.id,
        reading.url,
        SessionLocal,
    )
    return ReadingOut.from_orm_with_history(reading)


@router.delete("/{reading_id}", status_code=204)
def delete_reading(
    user_id: int,
    reading_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _get_user_or_404(user_id, db)
    _check_can_edit(current_user, user_id)
    reading = _get_reading_or_404(reading_id, user_id, db)
    reading_service.delete(db, reading)

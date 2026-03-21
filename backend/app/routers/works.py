import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..schemas import WorkCreate, WorkUpdate, WorkOut
from ..services import work_service

logger = logging.getLogger(__name__)
router = APIRouter(tags=["works"])


@router.get("/researchers/{researcher_id}/works", response_model=list[WorkOut])
def list_works(researcher_id: int, db: Session = Depends(get_db)):
    return work_service.list_by_researcher(db, researcher_id)


@router.post("/researchers/{researcher_id}/works", response_model=WorkOut, status_code=201)
def create_work(researcher_id: int, data: WorkCreate, db: Session = Depends(get_db)):
    return work_service.create(db, researcher_id, data)


@router.put("/works/{work_id}", response_model=WorkOut)
def update_work(work_id: int, data: WorkUpdate, db: Session = Depends(get_db)):
    work = work_service.get_by_id(db, work_id)
    if not work:
        raise HTTPException(status_code=404, detail="Work not found")
    return work_service.update(db, work, data)


@router.delete("/works/{work_id}", status_code=204)
def delete_work(work_id: int, db: Session = Depends(get_db)):
    work = work_service.get_by_id(db, work_id)
    if not work:
        raise HTTPException(status_code=404, detail="Work not found")
    work_service.delete(db, work)

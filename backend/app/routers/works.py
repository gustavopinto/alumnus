import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Work
from ..schemas import WorkCreate, WorkUpdate, WorkOut

logger = logging.getLogger(__name__)
router = APIRouter(tags=["works"])


@router.get("/researchers/{researcher_id}/works", response_model=list[WorkOut])
def list_works(researcher_id: int, db: Session = Depends(get_db)):
    return db.query(Work).filter(Work.researcher_id == researcher_id).order_by(Work.year.desc(), Work.id.desc()).all()


@router.post("/researchers/{researcher_id}/works", response_model=WorkOut, status_code=201)
def create_work(researcher_id: int, data: WorkCreate, db: Session = Depends(get_db)):
    work = Work(researcher_id=researcher_id, **data.model_dump())
    db.add(work)
    db.commit()
    db.refresh(work)
    logger.info("Work created: %s (%s) for researcher %s", work.title, work.type, researcher_id)
    return work


@router.put("/works/{work_id}", response_model=WorkOut)
def update_work(work_id: int, data: WorkUpdate, db: Session = Depends(get_db)):
    work = db.query(Work).get(work_id)
    if not work:
        raise HTTPException(status_code=404, detail="Work not found")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(work, key, value)
    db.commit()
    db.refresh(work)
    return work


@router.delete("/works/{work_id}", status_code=204)
def delete_work(work_id: int, db: Session = Depends(get_db)):
    work = db.query(Work).get(work_id)
    if not work:
        raise HTTPException(status_code=404, detail="Work not found")
    db.delete(work)
    db.commit()
    logger.info("Work deleted: id=%s", work_id)

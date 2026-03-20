import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Student
from ..schemas import StudentCreate, StudentUpdate, StudentOut
from ..slug import slugify

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/students", tags=["students"])


@router.get("/", response_model=list[StudentOut])
def list_students(ativo: bool | None = None, db: Session = Depends(get_db)):
    query = db.query(Student)
    if ativo is not None:
        query = query.filter(Student.ativo == ativo)
    return query.order_by(Student.nome).all()


@router.post("/", response_model=StudentOut, status_code=201)
def create_student(data: StudentCreate, db: Session = Depends(get_db)):
    student = Student(**data.model_dump())
    db.add(student)
    db.commit()
    db.refresh(student)
    logger.info("Student created: %s (id=%s)", student.nome, student.id)
    return student


@router.get("/by-slug/{slug}", response_model=StudentOut)
def get_student_by_slug(slug: str, db: Session = Depends(get_db)):
    students = db.query(Student).filter(Student.ativo == True).all()
    for s in students:
        if slugify(s.nome) == slug:
            return s
    raise HTTPException(status_code=404, detail="Student not found")


@router.get("/{student_id}", response_model=StudentOut)
def get_student(student_id: int, db: Session = Depends(get_db)):
    student = db.query(Student).get(student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    return student


@router.put("/{student_id}", response_model=StudentOut)
def update_student(student_id: int, data: StudentUpdate, db: Session = Depends(get_db)):
    student = db.query(Student).get(student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(student, key, value)
    db.commit()
    db.refresh(student)
    logger.info("Student updated: id=%s", student.id)
    return student


@router.delete("/{student_id}", status_code=204)
def deactivate_student(student_id: int, db: Session = Depends(get_db)):
    student = db.query(Student).get(student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    student.ativo = False
    db.commit()
    logger.info("Student deactivated: id=%s", student.id)

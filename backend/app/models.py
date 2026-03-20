from datetime import datetime

from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, JSON, Text, LargeBinary
from sqlalchemy.orm import relationship

from .database import Base


class Student(Base):
    __tablename__ = "students"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(255), nullable=False)
    photo_url = Column(String(500), nullable=True)
    status = Column(String(50), nullable=False)  # graduacao, mestrado, doutorado
    email = Column(String(255), nullable=True)
    orientador_id = Column(Integer, ForeignKey("students.id"), nullable=True)
    observacoes = Column(Text, nullable=True)
    ativo = Column(Boolean, default=True)
    registered = Column(Boolean, default=False)
    lattes_url = Column(String(500), nullable=True)
    scholar_url = Column(String(500), nullable=True)
    linkedin_url = Column(String(500), nullable=True)
    github_url = Column(String(500), nullable=True)
    interesses = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    orientador = relationship("Student", remote_side=[id])
    works = relationship("Work", back_populates="student", cascade="all, delete-orphan")
    notes = relationship("Note", back_populates="student", cascade="all, delete-orphan")


class Relationship(Base):
    __tablename__ = "relationships"

    id = Column(Integer, primary_key=True, index=True)
    source_student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    target_student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    relation_type = Column(String(50), nullable=False)  # orienta, coautor, mesmo_projeto, mesmo_laboratorio
    created_at = Column(DateTime, default=datetime.utcnow)

    source_student = relationship("Student", foreign_keys=[source_student_id])
    target_student = relationship("Student", foreign_keys=[target_student_id])


class Note(Base):
    __tablename__ = "notes"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    text = Column(Text, nullable=False)
    file_url = Column(String(500), nullable=True)
    file_name = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    student = relationship("Student", back_populates="notes")


class Work(Base):
    __tablename__ = "works"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    title = Column(String(500), nullable=False)
    type = Column(String(50), nullable=False)  # projeto, artigo, publicacao
    description = Column(Text, nullable=True)
    year = Column(Integer, nullable=True)
    url = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    student = relationship("Student", back_populates="works")


class User(Base):
    __tablename__ = "users"

    id            = Column(Integer, primary_key=True, index=True)
    email         = Column(String(255), unique=True, nullable=False, index=True)
    nome          = Column(String(255), nullable=False)
    password_hash = Column(String(255), nullable=False)
    role          = Column(String(20), nullable=False)  # professor, student
    student_id    = Column(Integer, ForeignKey("students.id"), nullable=True)
    created_at    = Column(DateTime, default=datetime.utcnow)

    student = relationship("Student", foreign_keys=[student_id])


class FileUpload(Base):
    __tablename__ = "file_uploads"

    id            = Column(Integer, primary_key=True, index=True)
    data          = Column(LargeBinary, nullable=False)
    mime_type     = Column(String(100), nullable=False)
    original_name = Column(String(255), nullable=False)
    created_at    = Column(DateTime, default=datetime.utcnow)


class GraphLayout(Base):
    __tablename__ = "graph_layouts"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), default="default")
    layout_jsonb = Column(JSON, default=dict)  # {student_id: {x, y}}
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

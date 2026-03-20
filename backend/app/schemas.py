from datetime import datetime
from typing import Optional

from pydantic import BaseModel, field_validator


# --- Student ---

class StudentCreate(BaseModel):
    nome: str
    photo_url: Optional[str] = None
    status: str
    email: Optional[str] = None
    orientador_id: Optional[int] = None
    observacoes: Optional[str] = None


class StudentUpdate(BaseModel):
    nome: Optional[str] = None
    photo_url: Optional[str] = None
    status: Optional[str] = None
    email: Optional[str] = None
    orientador_id: Optional[int] = None
    observacoes: Optional[str] = None
    ativo: Optional[bool] = None
    lattes_url: Optional[str] = None
    scholar_url: Optional[str] = None
    linkedin_url: Optional[str] = None
    github_url: Optional[str] = None
    interesses: Optional[str] = None


class StudentOut(BaseModel):
    id: int
    nome: str
    photo_url: Optional[str]
    status: str
    email: Optional[str]
    orientador_id: Optional[int]
    observacoes: Optional[str]
    ativo: bool
    registered: bool
    lattes_url: Optional[str]
    scholar_url: Optional[str]
    linkedin_url: Optional[str]
    github_url: Optional[str]
    interesses: Optional[str]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# --- Relationship ---

class RelationshipCreate(BaseModel):
    source_student_id: int
    target_student_id: int
    relation_type: str


class RelationshipUpdate(BaseModel):
    source_student_id: Optional[int] = None
    target_student_id: Optional[int] = None
    relation_type: Optional[str] = None


class RelationshipOut(BaseModel):
    id: int
    source_student_id: int
    target_student_id: int
    relation_type: str
    created_at: datetime

    model_config = {"from_attributes": True}


# --- Note ---

class NoteCreate(BaseModel):
    text: str


class NoteOut(BaseModel):
    id: int
    student_id: int
    text: str
    file_url: Optional[str]
    file_name: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}


# --- Work ---

class WorkCreate(BaseModel):
    title: str
    type: str  # projeto, artigo, publicacao
    description: Optional[str] = None
    year: Optional[int] = None
    url: Optional[str] = None


class WorkUpdate(BaseModel):
    title: Optional[str] = None
    type: Optional[str] = None
    description: Optional[str] = None
    year: Optional[int] = None
    url: Optional[str] = None


class WorkOut(BaseModel):
    id: int
    student_id: int
    title: str
    type: str
    description: Optional[str]
    year: Optional[int]
    url: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}


# --- Auth ---

class RegisterRequest(BaseModel):
    email:    str
    password: str

    @field_validator("password")
    @classmethod
    def password_length(cls, v):
        if len(v) < 8:
            raise ValueError("Senha deve ter ao menos 8 caracteres")
        return v


class LoginRequest(BaseModel):
    email:    str
    password: str


class TokenOut(BaseModel):
    access_token: str
    token_type:   str = "bearer"


class UserOut(BaseModel):
    id:         int
    email:      str
    nome:       str
    role:       str
    student_id: Optional[int]
    created_at: datetime

    model_config = {"from_attributes": True}


# --- Graph ---

class LayoutUpdate(BaseModel):
    positions: dict  # {student_id: {x, y}}

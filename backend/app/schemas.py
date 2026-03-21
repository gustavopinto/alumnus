import re
from datetime import datetime, date
from typing import Optional

from pydantic import BaseModel, field_validator

_INSTAGRAM_HANDLE = re.compile(r"^[A-Za-z0-9._]{1,30}$")
_TWITTER_HANDLE = re.compile(r"^[A-Za-z0-9_]{1,15}$")


# --- Researcher ---

class ResearcherCreate(BaseModel):
    nome: str
    photo_url: Optional[str] = None
    photo_thumb_url: Optional[str] = None
    status: str
    email: Optional[str] = None
    orientador_id: Optional[int] = None
    observacoes: Optional[str] = None


class ResearcherUpdate(BaseModel):
    nome: Optional[str] = None
    photo_url: Optional[str] = None
    photo_thumb_url: Optional[str] = None
    status: Optional[str] = None
    email: Optional[str] = None
    orientador_id: Optional[int] = None
    observacoes: Optional[str] = None
    ativo: Optional[bool] = None
    lattes_url: Optional[str] = None
    scholar_url: Optional[str] = None
    linkedin_url: Optional[str] = None
    github_url: Optional[str] = None
    instagram_url: Optional[str] = None
    twitter_url: Optional[str] = None
    whatsapp: Optional[str] = None
    interesses: Optional[str] = None
    matricula: Optional[str] = None
    curso: Optional[str] = None
    enrollment_date: Optional[date] = None

    @field_validator("instagram_url")
    @classmethod
    def validate_instagram_handle(cls, v):
        if v is None or (isinstance(v, str) and not v.strip()):
            return None
        s = str(v).strip().lstrip("@")
        if not _INSTAGRAM_HANDLE.match(s):
            raise ValueError(
                "Instagram: use o usuário com @ no início (1–30 caracteres: letras, números, . e _)"
            )
        return s

    @field_validator("twitter_url")
    @classmethod
    def validate_twitter_handle(cls, v):
        if v is None or (isinstance(v, str) and not v.strip()):
            return None
        s = str(v).strip().lstrip("@")
        if not _TWITTER_HANDLE.match(s):
            raise ValueError(
                "X/Twitter: use o usuário com @ no início (1–15 caracteres: letras, números e _)"
            )
        return s


class ResearcherOut(BaseModel):
    id: int
    nome: str
    photo_url: Optional[str]
    photo_thumb_url: Optional[str] = None
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
    instagram_url: Optional[str]
    twitter_url: Optional[str]
    whatsapp: Optional[str]
    interesses: Optional[str]
    matricula: Optional[str]
    curso: Optional[str]
    enrollment_date: Optional[date]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# --- Relationship ---

class RelationshipCreate(BaseModel):
    source_researcher_id: int
    target_researcher_id: int
    relation_type: str


class RelationshipUpdate(BaseModel):
    source_researcher_id: Optional[int] = None
    target_researcher_id: Optional[int] = None
    relation_type: Optional[str] = None


class RelationshipOut(BaseModel):
    id: int
    source_researcher_id: int
    target_researcher_id: int
    relation_type: str
    created_at: datetime

    model_config = {"from_attributes": True}


# --- Note ---

class NoteCreate(BaseModel):
    text: str


class NoteOut(BaseModel):
    id: int
    researcher_id: int
    text: str
    file_url: Optional[str]
    file_name: Optional[str]
    created_by_id: Optional[int] = None
    created_by_name: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}

    @classmethod
    def from_orm_with_creator(cls, note):
        obj = cls.model_validate(note)
        obj.created_by_id = note.created_by_id
        obj.created_by_name = note.created_by.nome if note.created_by else None
        return obj


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
    researcher_id: int
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
            raise ValueError("Password must be at least 8 characters")
        return v


class LoginRequest(BaseModel):
    email:    str
    password: str


class TokenOut(BaseModel):
    access_token: str
    token_type:   str = "bearer"


class UserOut(BaseModel):
    id:            int
    email:         str
    nome:          str
    role:          str
    researcher_id: Optional[int]
    last_login:    Optional[datetime]
    created_at:    datetime
    plan_type:     Optional[str] = None  # trial, monthly, annual — professor/superadmin
    plan_status:   Optional[str] = None  # active, expired
    account_activated_at: Optional[datetime] = None
    plan_period_ends_at: Optional[datetime] = None
    trial_days_remaining: Optional[int] = None  # só professor em trial; 0 se vencido

    model_config = {"from_attributes": True}


# --- Reminder ---

class ReminderCreate(BaseModel):
    text: str
    due_date: Optional[date] = None


class ReminderUpdate(BaseModel):
    text: Optional[str] = None
    due_date: Optional[date] = None
    done: Optional[bool] = None


class ReminderOut(BaseModel):
    id: int
    text: str
    due_date: Optional[date]
    done: bool
    created_at: datetime
    created_by_id: Optional[int] = None
    created_by_name: Optional[str] = None
    # True quando outro usuário criou o lembrete e o usuário atual ainda não marcou a notificação como lida
    notification_unread: bool = False

    model_config = {"from_attributes": True}


# --- Graph ---

class LayoutUpdate(BaseModel):
    positions: dict  # {researcher_id: {x, y}}


# --- Board ---

class BoardPostCreate(BaseModel):
    text: str


class BoardPostOut(BaseModel):
    id: int
    text: str
    author_id: Optional[int]
    author_name: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}

    @classmethod
    def from_orm_with_author(cls, post):
        obj = cls.model_validate(post)
        obj.author_name = post.author.nome if post.author else None
        return obj


# --- Manual ---

class ManualEntryCreate(BaseModel):
    question: str
    answer: str
    position: Optional[int] = 0


class ManualCommentOut(BaseModel):
    id: int
    entry_id: int
    text: str
    author_id: Optional[int]
    author_name: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}

    @classmethod
    def from_orm_with_author(cls, comment):
        obj = cls.model_validate(comment)
        obj.author_name = comment.author.nome if comment.author else None
        return obj


class ManualEntryOut(BaseModel):
    id: int
    question: str
    answer: str
    author_id: Optional[int]
    author_name: Optional[str] = None
    position: int
    vote_count: int = 0
    user_voted: bool = False
    comments: list[ManualCommentOut] = []
    created_at: datetime

    model_config = {"from_attributes": True}

    @classmethod
    def from_orm_with_context(cls, entry, current_user_id: Optional[int]):
        obj = cls.model_validate(entry)
        obj.author_name = entry.author.nome if entry.author else None
        obj.vote_count = len(entry.votes)
        obj.user_voted = any(v.user_id == current_user_id for v in entry.votes)
        obj.comments = [ManualCommentOut.from_orm_with_author(c) for c in entry.comments]
        return obj


class ManualCommentCreate(BaseModel):
    text: str


# --- Deadline interests ---

class DeadlineInterestOut(BaseModel):
    deadline_key: str
    user_id: int
    user_name: str
    user_photo_url: Optional[str] = None
    user_photo_thumb_url: Optional[str] = None
    profile_slug: Optional[str] = None

    model_config = {"from_attributes": True}

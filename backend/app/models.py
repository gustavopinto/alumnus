from datetime import datetime

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Date, ForeignKey, JSON, Text, LargeBinary, UniqueConstraint
from sqlalchemy.orm import relationship

from .database import Base


class Researcher(Base):
    __tablename__ = "researchers"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(255), nullable=False)
    photo_url = Column(String(500), nullable=True)
    # Miniatura quadrada (~64px) para deadlines; photo_url = retrato 3×4
    photo_thumb_url = Column(String(500), nullable=True)
    status = Column(String(50), nullable=False)  # graduacao, mestrado, doutorado
    email = Column(String(255), nullable=True)
    orientador_id = Column(Integer, ForeignKey("researchers.id"), nullable=True)
    observacoes = Column(Text, nullable=True)
    ativo = Column(Boolean, default=True)
    registered = Column(Boolean, default=False)
    lattes_url = Column(String(500), nullable=True)
    scholar_url = Column(String(500), nullable=True)
    linkedin_url = Column(String(500), nullable=True)
    github_url = Column(String(500), nullable=True)
    instagram_url = Column(String(50), nullable=True)
    twitter_url = Column(String(50), nullable=True)
    whatsapp = Column(String(20), nullable=True)
    interesses = Column(Text, nullable=True)
    matricula = Column(String(50), nullable=True)
    curso = Column(String(255), nullable=True)
    enrollment_date = Column(Date, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    orientador = relationship("Researcher", remote_side=[id])
    works = relationship("Work", back_populates="researcher", cascade="all, delete-orphan")
    notes = relationship("Note", back_populates="researcher", cascade="all, delete-orphan")


class Relationship(Base):
    __tablename__ = "relationships"

    id = Column(Integer, primary_key=True, index=True)
    source_researcher_id = Column(Integer, ForeignKey("researchers.id"), nullable=False)
    target_researcher_id = Column(Integer, ForeignKey("researchers.id"), nullable=False)
    relation_type = Column(String(50), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    source_researcher = relationship("Researcher", foreign_keys=[source_researcher_id])
    target_researcher = relationship("Researcher", foreign_keys=[target_researcher_id])


class Note(Base):
    __tablename__ = "notes"

    id = Column(Integer, primary_key=True, index=True)
    researcher_id = Column(Integer, ForeignKey("researchers.id"), nullable=False)
    text = Column(Text, nullable=False)
    file_url = Column(String(500), nullable=True)
    file_name = Column(String(255), nullable=True)
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    researcher = relationship("Researcher", back_populates="notes")
    created_by = relationship("User", foreign_keys=[created_by_id])


class Work(Base):
    __tablename__ = "works"

    id = Column(Integer, primary_key=True, index=True)
    researcher_id = Column(Integer, ForeignKey("researchers.id"), nullable=False)
    title = Column(String(500), nullable=False)
    type = Column(String(50), nullable=False)  # projeto, artigo, publicacao
    description = Column(Text, nullable=True)
    year = Column(Integer, nullable=True)
    url = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    researcher = relationship("Researcher", back_populates="works")


class User(Base):
    __tablename__ = "users"

    id            = Column(Integer, primary_key=True, index=True)
    email         = Column(String(255), unique=True, nullable=False, index=True)
    nome          = Column(String(255), nullable=False)
    password_hash = Column(String(255), nullable=False)
    role          = Column(String(20), nullable=False)  # professor, student
    is_admin      = Column(Boolean, nullable=False, default=False)
    researcher_id = Column(Integer, ForeignKey("researchers.id"), nullable=True)
    last_login    = Column(DateTime, nullable=True)
    created_at    = Column(DateTime, default=datetime.utcnow)
    # Apenas role=professor — ver app/plan.py
    plan_type     = Column(String(20), nullable=True)
    plan_status   = Column(String(20), nullable=True)  # active | expired
    account_activated_at = Column(DateTime, nullable=True)
    plan_period_ends_at  = Column(DateTime, nullable=True)

    researcher = relationship("Researcher", foreign_keys=[researcher_id])


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
    layout_jsonb = Column(JSON, default=dict)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Reminder(Base):
    __tablename__ = "reminders"

    id            = Column(Integer, primary_key=True, index=True)
    text          = Column(Text, nullable=False)
    due_date      = Column(Date, nullable=True)
    done          = Column(Boolean, default=False, nullable=False)
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at    = Column(DateTime, default=datetime.utcnow)

    created_by = relationship("User", foreign_keys=[created_by_id])



class BoardPost(Base):
    __tablename__ = "board_posts"

    id        = Column(Integer, primary_key=True, index=True)
    text      = Column(Text, nullable=False)
    author_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    author = relationship("User", foreign_keys=[author_id])


class ManualEntry(Base):
    __tablename__ = "manual_entries"

    id         = Column(Integer, primary_key=True, index=True)
    question   = Column(Text, nullable=False)
    answer     = Column(Text, nullable=False)
    author_id  = Column(Integer, ForeignKey("users.id"), nullable=True)
    position   = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    author   = relationship("User", foreign_keys=[author_id])
    votes    = relationship("ManualVote", back_populates="entry", cascade="all, delete-orphan")
    comments = relationship("ManualComment", back_populates="entry", cascade="all, delete-orphan", order_by="ManualComment.created_at")


class ManualVote(Base):
    __tablename__ = "manual_votes"

    entry_id = Column(Integer, ForeignKey("manual_entries.id", ondelete="CASCADE"), primary_key=True)
    user_id  = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)

    entry = relationship("ManualEntry", back_populates="votes")
    user  = relationship("User", foreign_keys=[user_id])


class DeadlineInterest(Base):
    __tablename__ = "deadline_interests"

    id           = Column(Integer, primary_key=True, index=True)
    deadline_key = Column(String(200), nullable=False)
    user_id      = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    created_at   = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", foreign_keys=[user_id])

    __table_args__ = (UniqueConstraint("deadline_key", "user_id"),)


class ManualComment(Base):
    __tablename__ = "manual_comments"

    id         = Column(Integer, primary_key=True, index=True)
    entry_id   = Column(Integer, ForeignKey("manual_entries.id", ondelete="CASCADE"), nullable=False)
    text       = Column(Text, nullable=False)
    author_id  = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    entry  = relationship("ManualEntry", back_populates="comments")
    author = relationship("User", foreign_keys=[author_id])

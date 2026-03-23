from datetime import datetime

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Date, ForeignKey, JSON, Text, LargeBinary, UniqueConstraint
from sqlalchemy.orm import relationship

from .database import Base


# ── Instituição ───────────────────────────────────────────────────────────────

class Institution(Base):
    __tablename__ = "institutions"

    id         = Column(Integer, primary_key=True, index=True)
    name       = Column(String(255), nullable=False)
    domain     = Column(String(255), unique=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    professor_institutions = relationship("ProfessorInstitution", back_populates="institution")
    groups                 = relationship("ResearchGroup", back_populates="institution")


# ── Professor ─────────────────────────────────────────────────────────────────

class Professor(Base):
    __tablename__ = "professors"

    id              = Column(Integer, primary_key=True, index=True)
    nome            = Column(String(255), nullable=False)
    ativo           = Column(Boolean, default=True)
    created_at      = Column(DateTime, default=datetime.utcnow)
    updated_at      = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user                   = relationship("User", back_populates="professor", uselist=False)
    professor_institutions = relationship("ProfessorInstitution", back_populates="professor", cascade="all, delete-orphan")
    professor_groups       = relationship("ProfessorGroup", back_populates="professor", cascade="all, delete-orphan")
    researchers            = relationship("Researcher", back_populates="orientador")


class ProfessorInstitution(Base):
    __tablename__ = "professor_institutions"

    id                  = Column(Integer, primary_key=True, index=True)
    professor_id        = Column(Integer, ForeignKey("professors.id", ondelete="CASCADE"), nullable=False)
    institution_id      = Column(Integer, ForeignKey("institutions.id"), nullable=False)
    institutional_email = Column(String(255), unique=True, nullable=False)
    created_at          = Column(DateTime, default=datetime.utcnow)

    professor   = relationship("Professor", back_populates="professor_institutions")
    institution = relationship("Institution", back_populates="professor_institutions")

    __table_args__ = (UniqueConstraint("professor_id", "institution_id"),)


# ── Grupo de pesquisa ─────────────────────────────────────────────────────────

class ResearchGroup(Base):
    __tablename__ = "research_groups"

    id             = Column(Integer, primary_key=True, index=True)
    name           = Column(String(255), nullable=False)
    institution_id = Column(Integer, ForeignKey("institutions.id"), nullable=True)
    created_at     = Column(DateTime, default=datetime.utcnow)

    institution      = relationship("Institution", back_populates="groups")
    professor_groups = relationship("ProfessorGroup", back_populates="group", cascade="all, delete-orphan")
    researchers      = relationship("Researcher", back_populates="group")


class ProfessorGroup(Base):
    __tablename__ = "professor_groups"

    professor_id   = Column(Integer, ForeignKey("professors.id", ondelete="CASCADE"), primary_key=True)
    group_id       = Column(Integer, ForeignKey("research_groups.id", ondelete="CASCADE"), primary_key=True)
    role_in_group  = Column(String(20), nullable=False, default="coordinator")
    institution_id = Column(Integer, ForeignKey("institutions.id"), nullable=True)
    created_at     = Column(DateTime, default=datetime.utcnow)

    professor   = relationship("Professor", back_populates="professor_groups")
    group       = relationship("ResearchGroup", back_populates="professor_groups")
    institution = relationship("Institution")


# ── Pesquisador (não-professor) ────────────────────────────────────────────────

class Researcher(Base):
    __tablename__ = "researchers"

    id               = Column(Integer, primary_key=True, index=True)
    nome             = Column(String(255), nullable=False)
    status           = Column(String(50), nullable=False)  # graduacao, mestrado, doutorado, postdoc
    email            = Column(String(255), nullable=True)
    group_id         = Column(Integer, ForeignKey("research_groups.id"), nullable=True)
    orientador_id    = Column(Integer, ForeignKey("professors.id"), nullable=True)
    observacoes      = Column(Text, nullable=True)
    ativo            = Column(Boolean, default=True)
    registered       = Column(Boolean, default=False)
    matricula        = Column(String(50), nullable=True)
    curso            = Column(String(255), nullable=True)
    enrollment_date  = Column(Date, nullable=True)
    created_at       = Column(DateTime, default=datetime.utcnow)
    updated_at       = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    orientador = relationship("Professor", back_populates="researchers")
    group      = relationship("ResearchGroup", back_populates="researchers")
    user       = relationship("User", primaryjoin="User.researcher_id == Researcher.id", foreign_keys="[User.researcher_id]", uselist=False, viewonly=True)

    works      = relationship("Work", back_populates="researcher", cascade="all, delete-orphan")
    notes      = relationship("Note", back_populates="researcher", cascade="all, delete-orphan")

    @property
    def photo_url(self) -> str | None:
        return self.user.photo_url if self.user else None

    @property
    def photo_thumb_url(self) -> str | None:
        return self.user.photo_thumb_url if self.user else None

    @property
    def orientador_nome(self) -> str | None:
        return self.orientador.nome if self.orientador else None


class Relationship(Base):
    __tablename__ = "relationships"

    id                   = Column(Integer, primary_key=True, index=True)
    source_researcher_id = Column(Integer, ForeignKey("researchers.id"), nullable=False)
    target_researcher_id = Column(Integer, ForeignKey("researchers.id"), nullable=False)
    relation_type        = Column(String(50), nullable=False)
    created_at           = Column(DateTime, default=datetime.utcnow)

    source_researcher = relationship("Researcher", foreign_keys=[source_researcher_id])
    target_researcher = relationship("Researcher", foreign_keys=[target_researcher_id])


class Note(Base):
    __tablename__ = "notes"

    id            = Column(Integer, primary_key=True, index=True)
    researcher_id = Column(Integer, ForeignKey("researchers.id"), nullable=False)
    text          = Column(Text, nullable=False)
    file_url      = Column(String(500), nullable=True)
    file_name     = Column(String(255), nullable=True)
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at    = Column(DateTime, default=datetime.utcnow)

    researcher = relationship("Researcher", back_populates="notes")
    created_by = relationship("User", foreign_keys=[created_by_id])


class Work(Base):
    __tablename__ = "works"

    id            = Column(Integer, primary_key=True, index=True)
    researcher_id = Column(Integer, ForeignKey("researchers.id"), nullable=False)
    title         = Column(String(500), nullable=False)
    type          = Column(String(50), nullable=False)
    description   = Column(Text, nullable=True)
    year          = Column(Integer, nullable=True)
    url           = Column(String(500), nullable=True)
    created_at    = Column(DateTime, default=datetime.utcnow)

    researcher = relationship("Researcher", back_populates="works")


class User(Base):
    __tablename__ = "users"

    id                   = Column(Integer, primary_key=True, index=True)
    email                = Column(String(255), unique=True, nullable=False, index=True)
    nome                 = Column(String(255), nullable=False)
    password_hash        = Column(String(255), nullable=False)
    role                 = Column(String(20), nullable=False)  # superadmin | professor | student
    is_admin             = Column(Boolean, nullable=False, default=False)  # computed from role
    professor_id         = Column(Integer, ForeignKey("professors.id"), nullable=True)
    researcher_id        = Column(Integer, ForeignKey("researchers.id"), nullable=True)
    last_login           = Column(DateTime, nullable=True)
    plan_type            = Column(String(20), nullable=True)
    plan_status          = Column(String(20), nullable=True)
    account_activated_at = Column(DateTime, nullable=True)
    plan_period_ends_at  = Column(DateTime, nullable=True)
    photo_url            = Column(String(500), nullable=True)
    photo_thumb_url      = Column(String(500), nullable=True)
    lattes_url           = Column(String(500), nullable=True)
    scholar_url          = Column(String(500), nullable=True)
    linkedin_url         = Column(String(500), nullable=True)
    github_url           = Column(String(500), nullable=True)
    instagram_url        = Column(String(50), nullable=True)
    twitter_url          = Column(String(50), nullable=True)
    whatsapp             = Column(String(20), nullable=True)
    interesses           = Column(Text, nullable=True)
    bio                  = Column(Text, nullable=True)
    created_at           = Column(DateTime, default=datetime.utcnow)

    professor  = relationship("Professor", back_populates="user", foreign_keys=[professor_id])
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

    id           = Column(Integer, primary_key=True, index=True)
    name         = Column(String(100), default="default")
    layout_jsonb = Column(JSON, default=dict)
    updated_at   = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Reminder(Base):
    __tablename__ = "reminders"

    id            = Column(Integer, primary_key=True, index=True)
    text          = Column(Text, nullable=False)
    due_date      = Column(Date, nullable=True)
    done          = Column(Boolean, default=False, nullable=False)
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at    = Column(DateTime, default=datetime.utcnow)

    created_by = relationship("User", foreign_keys=[created_by_id])



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

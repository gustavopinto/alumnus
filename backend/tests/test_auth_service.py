"""
Unit tests for app/services/auth_service.py

Covers:
- _norm_email
- user_email_exists
- get_active_researcher_for_email
- create_student_from_researcher
- authenticate
- record_login
"""

from datetime import datetime

import pytest
from passlib.context import CryptContext

from app.services import auth_service
from app.schemas import RegisterRequest
from app.models import User, Researcher

from .conftest import make_researcher, make_user

pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")


# ---------------------------------------------------------------------------
# user_email_exists
# ---------------------------------------------------------------------------

class TestUserEmailExists:
    def test_returns_false_when_no_users(self, db):
        assert auth_service.user_email_exists(db, "nobody@example.com") is False

    def test_returns_true_for_existing_email(self, db):
        make_user(db, email="existing@univ.edu.br")
        assert auth_service.user_email_exists(db, "existing@univ.edu.br") is True

    def test_case_insensitive_match(self, db):
        make_user(db, email="user@univ.edu.br")
        assert auth_service.user_email_exists(db, "USER@UNIV.EDU.BR") is True

    def test_strips_whitespace_before_check(self, db):
        make_user(db, email="spaced@univ.edu.br")
        assert auth_service.user_email_exists(db, "  spaced@univ.edu.br  ") is True

    def test_different_email_returns_false(self, db):
        make_user(db, email="a@univ.edu.br")
        assert auth_service.user_email_exists(db, "b@univ.edu.br") is False


# ---------------------------------------------------------------------------
# get_active_researcher_for_email
# ---------------------------------------------------------------------------

class TestGetActiveResearcherForEmail:
    def test_returns_none_when_no_researcher(self, db):
        result = auth_service.get_active_researcher_for_email(db, "ghost@univ.edu.br")
        assert result is None

    def test_returns_active_researcher_by_email(self, db):
        r = make_researcher(db, email="active@univ.edu.br", ativo=True)
        result = auth_service.get_active_researcher_for_email(db, "active@univ.edu.br")
        assert result is not None
        assert result.id == r.id

    def test_returns_none_for_inactive_researcher(self, db):
        make_researcher(db, email="inactive@univ.edu.br", ativo=False)
        result = auth_service.get_active_researcher_for_email(db, "inactive@univ.edu.br")
        assert result is None

    def test_case_insensitive_email_lookup(self, db):
        r = make_researcher(db, email="cased@univ.edu.br", ativo=True)
        result = auth_service.get_active_researcher_for_email(db, "CASED@UNIV.EDU.BR")
        assert result is not None
        assert result.id == r.id

    def test_strips_whitespace(self, db):
        r = make_researcher(db, email="ws@univ.edu.br", ativo=True)
        result = auth_service.get_active_researcher_for_email(db, "  ws@univ.edu.br  ")
        assert result is not None
        assert result.id == r.id


# ---------------------------------------------------------------------------
# create_student_from_researcher
# ---------------------------------------------------------------------------

class TestCreateStudentFromResearcher:
    def test_creates_user_with_correct_fields(self, db):
        researcher = make_researcher(db, nome="Joao Neto", email="joao@univ.edu.br")
        req = RegisterRequest(email="joao@univ.edu.br", password="password123")
        user = auth_service.create_student_from_researcher(db, req, researcher, pwd_ctx)

        assert user.id is not None
        assert user.email == "joao@univ.edu.br"
        assert user.nome == "Joao Neto"
        assert user.role == "student"
        assert user.researcher_id == researcher.id

    def test_password_is_hashed(self, db):
        researcher = make_researcher(db, email="hash@univ.edu.br")
        req = RegisterRequest(email="hash@univ.edu.br", password="plaintext9")
        user = auth_service.create_student_from_researcher(db, req, researcher, pwd_ctx)

        assert user.password_hash != "plaintext9"
        assert pwd_ctx.verify("plaintext9", user.password_hash)

    def test_marks_researcher_as_registered(self, db):
        researcher = make_researcher(db, email="mark@univ.edu.br", registered=False)
        req = RegisterRequest(email="mark@univ.edu.br", password="password99")
        auth_service.create_student_from_researcher(db, req, researcher, pwd_ctx)

        db.refresh(researcher)
        assert researcher.registered is True

    def test_user_is_persisted_to_db(self, db):
        researcher = make_researcher(db, email="persist@univ.edu.br")
        req = RegisterRequest(email="persist@univ.edu.br", password="persisted1")
        user = auth_service.create_student_from_researcher(db, req, researcher, pwd_ctx)

        fetched = db.query(User).filter(User.id == user.id).first()
        assert fetched is not None
        assert fetched.email == "persist@univ.edu.br"


# ---------------------------------------------------------------------------
# authenticate
# ---------------------------------------------------------------------------

class TestAuthenticate:
    def test_returns_user_with_correct_credentials(self, db):
        make_user(db, email="login@univ.edu.br", password="correct123")
        user = auth_service.authenticate(db, "login@univ.edu.br", "correct123", pwd_ctx)
        assert user is not None
        assert user.email == "login@univ.edu.br"

    def test_returns_none_for_wrong_password(self, db):
        make_user(db, email="wrong@univ.edu.br", password="correct123")
        result = auth_service.authenticate(db, "wrong@univ.edu.br", "wrongpassword", pwd_ctx)
        assert result is None

    def test_returns_none_for_nonexistent_user(self, db):
        result = auth_service.authenticate(db, "nobody@univ.edu.br", "anypassword", pwd_ctx)
        assert result is None

    def test_case_insensitive_email(self, db):
        make_user(db, email="ci@univ.edu.br", password="password1")
        user = auth_service.authenticate(db, "CI@UNIV.EDU.BR", "password1", pwd_ctx)
        assert user is not None

    def test_strips_whitespace_from_email(self, db):
        make_user(db, email="strip@univ.edu.br", password="passpass1")
        user = auth_service.authenticate(db, "  strip@univ.edu.br  ", "passpass1", pwd_ctx)
        assert user is not None


# ---------------------------------------------------------------------------
# record_login
# ---------------------------------------------------------------------------

class TestRecordLogin:
    def test_sets_last_login_timestamp(self, db):
        user = make_user(db, email="rlogin@univ.edu.br")
        assert user.last_login is None

        auth_service.record_login(db, user)

        db.refresh(user)
        assert user.last_login is not None
        assert isinstance(user.last_login, datetime)

    def test_last_login_is_recent(self, db):
        user = make_user(db, email="recent@univ.edu.br")
        before = datetime.utcnow()
        auth_service.record_login(db, user)
        after = datetime.utcnow()

        db.refresh(user)
        assert before <= user.last_login <= after

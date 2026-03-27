"""
Unit tests for app/services/auth_service.py

Covers:
- _norm_email (via user_email_exists)
- user_email_exists
- activate_account
- authenticate
- record_login
"""

from datetime import datetime

import pytest
from passlib.context import CryptContext

from app.services import auth_service
from app.schemas import RegisterRequest
from app.models import User

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
# activate_account
# ---------------------------------------------------------------------------

class TestActivateAccount:
    def test_activates_pending_account(self, db):
        make_researcher(db, email="pending@univ.edu.br", password=None)
        req = RegisterRequest(email="pending@univ.edu.br", password="newpassword1")
        user = auth_service.activate_account(db, req, pwd_ctx)

        assert user.id is not None
        assert user.email == "pending@univ.edu.br"
        assert user.password_hash is not None
        assert pwd_ctx.verify("newpassword1", user.password_hash)

    def test_returns_404_for_unknown_email(self, db):
        from fastapi import HTTPException
        req = RegisterRequest(email="ghost@univ.edu.br", password="password1")
        with pytest.raises(HTTPException) as exc:
            auth_service.activate_account(db, req, pwd_ctx)
        assert exc.value.status_code == 404

    def test_returns_409_for_already_active_account(self, db):
        from fastapi import HTTPException
        make_user(db, email="active@univ.edu.br", password="existing123")
        req = RegisterRequest(email="active@univ.edu.br", password="newpassword1")
        with pytest.raises(HTTPException) as exc:
            auth_service.activate_account(db, req, pwd_ctx)
        assert exc.value.status_code == 409

    def test_role_preserved_after_activation(self, db):
        make_researcher(db, email="role@univ.edu.br", password=None)
        req = RegisterRequest(email="role@univ.edu.br", password="password11")
        user = auth_service.activate_account(db, req, pwd_ctx)
        assert user.role == "researcher"


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

    def test_returns_none_for_pending_account(self, db):
        """Conta pendente (password_hash=None) não pode autenticar."""
        make_researcher(db, email="pending@univ.edu.br", password=None)
        result = auth_service.authenticate(db, "pending@univ.edu.br", "anypassword", pwd_ctx)
        assert result is None


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

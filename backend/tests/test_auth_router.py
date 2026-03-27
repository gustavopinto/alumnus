"""
Unit tests for app/routers/auth.py

Covers:
- make_token
- POST /auth/register
- POST /auth/login
- GET  /auth/me
"""

from datetime import datetime, timedelta
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from jose import jwt

from app.main import app
from app.database import get_db
from app.deps import get_current_user, SECRET_KEY, ALGORITHM
from app.models import User
from app.routers.auth import make_token

from .conftest import make_researcher, make_user, pwd_ctx


# ---------------------------------------------------------------------------
# make_token (unit test — no HTTP)
# ---------------------------------------------------------------------------

class TestMakeToken:
    def test_token_contains_user_id(self, db):
        user = make_user(db, email="tok@univ.edu.br", role="researcher")
        token = make_token(user)
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        assert payload["sub"] == str(user.id)

    def test_token_contains_role(self, db):
        user = make_user(db, email="tok2@univ.edu.br", role="professor")
        token = make_token(user)
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        assert payload["role"] == "professor"

    def test_token_is_admin_true_for_superadmin_role(self, db):
        user = make_user(db, email="adm_tok@univ.edu.br", role="superadmin")
        token = make_token(user)
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        assert payload["is_admin"] is True

    def test_token_is_admin_false_for_student(self, db):
        user = make_user(db, email="stu_tok@univ.edu.br", role="researcher")
        token = make_token(user)
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        assert payload["is_admin"] is False

    def test_token_has_exp_field(self, db):
        user = make_user(db, email="exp_tok@univ.edu.br", role="researcher")
        token = make_token(user)
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        assert "exp" in payload


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def http_client(db):
    def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app, raise_server_exceptions=True) as c:
        yield c, db
    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# POST /auth/register
# ---------------------------------------------------------------------------

class TestRegister:
    def test_successful_registration(self, http_client):
        client, db = http_client
        make_researcher(db, nome="Novo Aluno", email="novo@univ.edu.br", ativo=True)

        resp = client.post("/api/auth/register", json={
            "email": "novo@univ.edu.br",
            "password": "strongpass1",
        })
        assert resp.status_code == 201
        data = resp.json()
        assert data["email"] == "novo@univ.edu.br"
        assert data["role"] == "researcher"

    def test_duplicate_email_returns_409(self, http_client):
        client, db = http_client
        make_researcher(db, nome="Dup Aluno", email="dup@univ.edu.br", ativo=True)
        # First registration
        client.post("/api/auth/register", json={"email": "dup@univ.edu.br", "password": "strongpass1"})
        # Second registration with same email
        resp = client.post("/api/auth/register", json={"email": "dup@univ.edu.br", "password": "anotherpass"})
        assert resp.status_code == 409

    def test_email_not_in_researcher_returns_404(self, http_client):
        client, db = http_client
        resp = client.post("/api/auth/register", json={
            "email": "ghost@univ.edu.br",
            "password": "strongpass1",
        })
        assert resp.status_code == 404

    def test_unknown_email_returns_404(self, http_client):
        client, db = http_client
        # No new self-registration; accounts must be pre-created by admin
        resp = client.post("/api/auth/register", json={
            "email": "nobody@gmail.com",
            "password": "strongpass1",
        })
        assert resp.status_code == 404

    def test_password_too_short_returns_422(self, http_client):
        client, db = http_client
        resp = client.post("/api/auth/register", json={
            "email": "short@univ.edu.br",
            "password": "1234567",
        })
        assert resp.status_code == 422

    def test_inactive_researcher_returns_404(self, http_client):
        client, db = http_client
        make_researcher(db, nome="Inativo", email="inativo@univ.edu.br", ativo=False)

        resp = client.post("/api/auth/register", json={
            "email": "inativo@univ.edu.br",
            "password": "strongpass1",
        })
        assert resp.status_code == 404

    def test_email_normalized_before_lookup(self, http_client):
        client, db = http_client
        make_researcher(db, nome="Case Aluno", email="case@univ.edu.br", ativo=True)

        resp = client.post("/api/auth/register", json={
            "email": "CASE@UNIV.EDU.BR",
            "password": "strongpass1",
        })
        assert resp.status_code == 201

    def test_registered_researcher_marks_registered_true(self, http_client):
        client, db = http_client
        researcher = make_researcher(db, nome="Mark R", email="markr@univ.edu.br", ativo=True)

        client.post("/api/auth/register", json={"email": "markr@univ.edu.br", "password": "strongpass1"})
        db.refresh(researcher)
        assert researcher.registered is True


# ---------------------------------------------------------------------------
# POST /auth/login
# ---------------------------------------------------------------------------

class TestLogin:
    def test_successful_login_returns_token(self, http_client):
        client, db = http_client
        make_user(db, email="login@univ.edu.br", password="correctpass")

        resp = client.post("/api/auth/login", json={
            "email": "login@univ.edu.br",
            "password": "correctpass",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_wrong_password_returns_401(self, http_client):
        client, db = http_client
        make_user(db, email="wrongpw@univ.edu.br", password="correctpass")

        resp = client.post("/api/auth/login", json={
            "email": "wrongpw@univ.edu.br",
            "password": "wrongpassword",
        })
        assert resp.status_code == 401

    def test_nonexistent_user_returns_401(self, http_client):
        client, db = http_client
        resp = client.post("/api/auth/login", json={
            "email": "nobody@univ.edu.br",
            "password": "any",
        })
        assert resp.status_code == 401

    def test_login_records_last_login(self, http_client):
        client, db = http_client
        user = make_user(db, email="lastlogin@univ.edu.br", password="testpass9")
        assert user.last_login is None

        client.post("/api/auth/login", json={"email": "lastlogin@univ.edu.br", "password": "testpass9"})
        db.refresh(user)
        assert user.last_login is not None

    def test_token_is_decodeable(self, http_client):
        client, db = http_client
        make_user(db, email="decode@univ.edu.br", password="decodepass")

        resp = client.post("/api/auth/login", json={"email": "decode@univ.edu.br", "password": "decodepass"})
        token = resp.json()["access_token"]
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        assert payload["email"] == "decode@univ.edu.br"

    def test_case_insensitive_email_login(self, http_client):
        client, db = http_client
        make_user(db, email="ci_login@univ.edu.br", password="cipassword")

        resp = client.post("/api/auth/login", json={
            "email": "CI_LOGIN@UNIV.EDU.BR",
            "password": "cipassword",
        })
        assert resp.status_code == 200


# ---------------------------------------------------------------------------
# GET /auth/me
# ---------------------------------------------------------------------------

class TestMe:
    def test_me_returns_current_user(self, db):
        user = make_user(db, email="me@univ.edu.br", role="professor",
                         plan_type="trial", plan_status="active",
                         account_activated_at=datetime.utcnow(),
                         plan_period_ends_at=datetime.utcnow() + timedelta(days=25))

        def override_get_db():
            yield db

        def override_get_current_user():
            return user

        app.dependency_overrides[get_db] = override_get_db
        app.dependency_overrides[get_current_user] = override_get_current_user

        with TestClient(app) as c:
            resp = c.get("/api/auth/me")

        app.dependency_overrides.clear()

        assert resp.status_code == 200
        data = resp.json()
        assert data["email"] == "me@univ.edu.br"
        assert data["role"] == "professor"

    def test_me_without_auth_returns_403_or_401(self, http_client):
        client, db = http_client
        resp = client.get("/api/auth/me")
        assert resp.status_code in (401, 403)

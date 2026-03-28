"""Tests for app/services/user_service.py"""
import pytest
from passlib.context import CryptContext

from app.models import User
from app.services import user_service

pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")


def make_user(db, email="u@test.br"):
    u = User(
        email=email,
        nome="Test User",
        password_hash=pwd_ctx.hash("pass"),
        role="researcher",
    )
    db.add(u)
    db.commit()
    db.refresh(u)
    return u


class TestGetById:
    def test_returns_user(self, db):
        u = make_user(db)
        found = user_service.get_by_id(db, u.id)
        assert found is not None
        assert found.id == u.id

    def test_returns_none_for_unknown(self, db):
        assert user_service.get_by_id(db, 9999) is None


class TestUpdateProfile:
    def test_updates_nome(self, db):
        u = make_user(db, "upd@test.br")
        result = user_service.update_profile(db, u, {"nome": "Novo Nome"})
        assert result.nome == "Novo Nome"

    def test_updates_password_when_provided(self, db):
        u = make_user(db, "pw@test.br")
        old_hash = u.password_hash
        user_service.update_profile(db, u, {"password": "newpassword123"})
        assert u.password_hash != old_hash

    def test_ignores_empty_password(self, db):
        u = make_user(db, "nopw@test.br")
        old_hash = u.password_hash
        user_service.update_profile(db, u, {"password": ""})
        assert u.password_hash == old_hash

    def test_ignores_none_password(self, db):
        u = make_user(db, "nullpw@test.br")
        old_hash = u.password_hash
        user_service.update_profile(db, u, {"password": None})
        assert u.password_hash == old_hash

    def test_updates_bio(self, db):
        u = make_user(db, "bio@test.br")
        user_service.update_profile(db, u, {"bio": "Minha bio"})
        assert u.bio == "Minha bio"

    def test_updates_lattes_url(self, db):
        u = make_user(db, "lattes@test.br")
        user_service.update_profile(db, u, {"lattes_url": "http://lattes.cnpq.br/123"})
        assert u.lattes_url == "http://lattes.cnpq.br/123"

    def test_ignores_unknown_fields(self, db):
        u = make_user(db, "unknown@test.br")
        user_service.update_profile(db, u, {"nonexistent_field": "value"})
        assert u.nome == "Test User"

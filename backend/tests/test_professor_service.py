"""Tests for app/services/professor_service.py"""
import pytest
from passlib.context import CryptContext

from app.models import Professor, User
from app.services import professor_service

pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")


def make_professor(db, nome="Prof Test", email="prof@test.br", ativo=True):
    prof = Professor()
    db.add(prof)
    db.flush()
    user = User(
        email=email,
        nome=nome,
        password_hash=pwd_ctx.hash("pass"),
        role="professor",
        ativo=ativo,
        professor_id=prof.id,
    )
    db.add(user)
    db.commit()
    db.refresh(prof)
    db.refresh(user)
    return prof, user


class TestGetById:
    def test_returns_professor(self, db):
        prof, _ = make_professor(db)
        found = professor_service.get_by_id(db, prof.id)
        assert found is not None
        assert found.id == prof.id

    def test_returns_none_for_unknown(self, db):
        assert professor_service.get_by_id(db, 9999) is None


class TestGetByUser:
    def test_returns_professor_from_user(self, db):
        prof, user = make_professor(db, "Prof By User", "byuser@test.br")
        found = professor_service.get_by_user(db, user)
        assert found is not None
        assert found.id == prof.id

    def test_returns_none_when_user_has_no_professor_id(self, db):
        user = User(
            email="noprof@test.br",
            nome="No Prof",
            password_hash=pwd_ctx.hash("pass"),
            role="researcher",
            )
        db.add(user)
        db.commit()
        db.refresh(user)
        assert professor_service.get_by_user(db, user) is None


class TestListActive:
    def test_returns_only_active_professors(self, db):
        prof_active, _ = make_professor(db, "Prof Ativo", "ativo@test.br", ativo=True)
        prof_inactive, _ = make_professor(db, "Prof Inativo", "inativo@test.br", ativo=False)
        result = professor_service.list_active(db)
        ids = [p.id for p in result]
        assert prof_active.id in ids
        assert prof_inactive.id not in ids

    def test_ordered_by_nome(self, db):
        make_professor(db, "Zara Prof", "zara@test.br")
        make_professor(db, "Ana Prof", "ana@test.br")
        result = professor_service.list_active(db)
        names = [p.nome for p in result]
        assert names == sorted(names)


class TestUpdate:
    def test_updates_nome(self, db):
        prof, _ = make_professor(db, "Prof Old Name", "oldname@test.br")
        updated = professor_service.update(db, prof, {"nome": "Prof New Name"})
        assert updated.nome == "Prof New Name"

    def test_ignores_unknown_fields(self, db):
        prof, _ = make_professor(db, "Prof Unknown", "unknown@test.br")
        professor_service.update(db, prof, {"nonexistent_field": "value"})
        assert prof.nome == "Prof Unknown"


class TestDeactivate:
    def test_deactivates_professor(self, db):
        prof, _ = make_professor(db, "Prof Active Deact", "deact@test.br")
        assert prof.ativo is True
        professor_service.deactivate(db, prof)
        assert prof.ativo is False

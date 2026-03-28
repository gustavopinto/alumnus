"""Tests for app/routers/groups.py"""
from passlib.context import CryptContext

from app.models import Institution, Professor, ProfessorInstitution, User
from app.routers.auth import make_token
from app.services import group_service

from .conftest import make_user

pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")


def make_professor_user(db, nome="Prof Groups Router", email="profgr@univ.br"):
    prof = Professor()
    db.add(prof)
    db.flush()
    user = User(
        email=email,
        nome=nome,
        password_hash=pwd_ctx.hash("pass"),
        role="professor",
        professor_id=prof.id,
    )
    db.add(user)
    db.commit()
    db.refresh(prof)
    db.refresh(user)
    return prof, user


def make_institution(db, name="GR_INST", domain="grinst.br"):
    inst = Institution(name=name, domain=domain)
    db.add(inst)
    db.commit()
    db.refresh(inst)
    return inst


class TestListMyGroups:
    def test_superadmin_lists_all_groups(self, client, db):
        user = make_user(db, email="sagroups@univ.br", role="superadmin")
        token = make_token(user)
        resp = client.get("/api/groups/", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_researcher_returns_groups(self, client, db):
        user = make_user(db, email="rgroupslist@univ.br", role="researcher")
        token = make_token(user)
        resp = client.get("/api/groups/", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_professor_lists_own_groups(self, client, db):
        prof, user = make_professor_user(db, "Prof List Groups", "proflistg@univ.br")
        inst = make_institution(db, "LISTG_INST", "listginst.br")
        group_service.create_group(db, prof, "Grupo Do Prof", inst.id)
        token = make_token(user)
        resp = client.get("/api/groups/", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        assert len(resp.json()) >= 1

    def test_professor_without_profile_returns_empty(self, client, db):
        # Professor role user without Professor record
        user = make_user(db, email="profnoprofile@univ.br", role="professor")
        token = make_token(user)
        resp = client.get("/api/groups/", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        assert resp.json() == []


class TestCreateGroup:
    def test_professor_creates_group(self, client, db):
        prof, user = make_professor_user(db, "Prof Create G", "profcg@univ.br")
        inst = make_institution(db, "CGTEST", "cgtest.br")
        token = make_token(user)
        resp = client.post(
            "/api/groups/",
            json={"name": "Novo Grupo", "institution_id": inst.id},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 201
        assert resp.json()["name"] == "Novo Grupo"
        assert resp.json()["institution_id"] == inst.id

    def test_researcher_cannot_create_group(self, client, db):
        inst = make_institution(db, "RCINST", "rcinst.br")
        user = make_user(db, email="rgroupcreate@univ.br", role="researcher")
        token = make_token(user)
        resp = client.post(
            "/api/groups/",
            json={"name": "Grupo R", "institution_id": inst.id},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 403


class TestUpdateGroup:
    def test_coordinator_can_update(self, client, db):
        prof, user = make_professor_user(db, "Prof Update G", "profug@univ.br")
        inst = make_institution(db, "UGINST", "uginst.br")
        group = group_service.create_group(db, prof, "Grupo Original", inst.id)
        token = make_token(user)
        resp = client.patch(
            f"/api/groups/{group.id}",
            json={"name": "Grupo Atualizado"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["name"] == "Grupo Atualizado"

    def test_returns_404_for_unknown(self, client, db):
        _, user = make_professor_user(db, "Prof 404G", "prof404g@univ.br")
        token = make_token(user)
        resp = client.patch("/api/groups/9999", json={"name": "X"}, headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 404


class TestGetGroupMembers:
    def test_returns_404_for_unknown_group(self, client, db):
        _, user = make_professor_user(db, "Prof G404 Members", "profg404m@univ.br")
        token = make_token(user)
        resp = client.get("/api/groups/9999/members", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 404

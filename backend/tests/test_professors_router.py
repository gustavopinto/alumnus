"""Tests for app/routers/professors.py"""
from passlib.context import CryptContext

from app.models import Professor, User
from app.routers.auth import make_token

from .conftest import make_user

pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")


def make_professor_user(db, nome="Prof Router", email="profrouter@univ.br"):
    prof = Professor(nome=nome, ativo=True)
    db.add(prof)
    db.flush()
    user = User(
        email=email,
        nome=nome,
        password_hash=pwd_ctx.hash("pass"),
        role="professor",
        is_admin=False,
        professor_id=prof.id,
    )
    db.add(user)
    db.commit()
    db.refresh(prof)
    db.refresh(user)
    return prof, user


class TestListProfessors:
    def test_professor_can_list(self, client, db):
        _, user = make_professor_user(db, "Prof List Router", "proflist_r@univ.br")
        token = make_token(user)
        resp = client.get("/api/professors/", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_researcher_cannot_list(self, client, db):
        user = make_user(db, email="rlistprof@univ.br", role="researcher")
        token = make_token(user)
        resp = client.get("/api/professors/", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 403

    def test_requires_auth(self, client, db):
        resp = client.get("/api/professors/")
        assert resp.status_code in (401, 403)

    def test_only_active_professors_listed(self, client, db):
        prof, user = make_professor_user(db, "Prof Active List", "active_list@univ.br")
        token = make_token(user)
        resp = client.get("/api/professors/", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        # Active professor should be in the list
        ids = [p["id"] for p in resp.json()]
        assert prof.id in ids


class TestGetProfessor:
    def test_get_by_id(self, client, db):
        prof, user = make_professor_user(db, "Prof Get Router", "profget_r@univ.br")
        token = make_token(user)
        resp = client.get(f"/api/professors/{prof.id}", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        assert resp.json()["id"] == prof.id
        assert resp.json()["nome"] == "Prof Get Router"

    def test_returns_404_for_unknown(self, client, db):
        _, user = make_professor_user(db, "Prof 404 Get", "prof404get@univ.br")
        token = make_token(user)
        resp = client.get("/api/professors/9999", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 404


class TestUpdateProfessor:
    def test_professor_updates_own(self, client, db):
        prof, user = make_professor_user(db, "Prof Update Router", "profupdate_r@univ.br")
        token = make_token(user)
        resp = client.put(
            f"/api/professors/{prof.id}",
            json={"nome": "Prof Updated Router"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["nome"] == "Prof Updated Router"

    def test_returns_404_for_unknown(self, client, db):
        _, user = make_professor_user(db, "Prof 404 Update", "prof404upd@univ.br")
        token = make_token(user)
        resp = client.put(
            "/api/professors/9999",
            json={"nome": "X"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 404

    def test_professor_cannot_update_other(self, client, db):
        prof1, _ = make_professor_user(db, "Prof Owner", "profowner@univ.br")
        _, user2 = make_professor_user(db, "Prof Other", "profother@univ.br")
        token = make_token(user2)
        resp = client.put(
            f"/api/professors/{prof1.id}",
            json={"nome": "Unauthorized"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 403

"""Tests for app/routers/institutions.py"""
from passlib.context import CryptContext

from app.models import Professor, User
from app.routers.auth import make_token
from app.services import institution_service

from .conftest import make_user

pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")


def make_professor_user(db, nome="Prof Inst Router", email="profir@univ.br"):
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


class TestListInstitutions:
    def test_superadmin_can_list(self, client, db):
        user = make_user(db, email="sainst@univ.br", role="superadmin")
        token = make_token(user)
        resp = client.get("/api/institutions/", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_professor_cannot_list(self, client, db):
        _, user = make_professor_user(db)
        token = make_token(user)
        resp = client.get("/api/institutions/", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 403

    def test_researcher_cannot_list(self, client, db):
        user = make_user(db, email="rinst@univ.br", role="researcher")
        token = make_token(user)
        resp = client.get("/api/institutions/", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 403


class TestCreateInstitution:
    def test_superadmin_creates_institution(self, client, db):
        user = make_user(db, email="sacreate@univ.br", role="superadmin")
        token = make_token(user)
        resp = client.post(
            "/api/institutions/",
            json={"email": "admin@newinst.br"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 201
        assert resp.json()["domain"] == "newinst.br"

    def test_creates_research_group_for_institution(self, client, db):
        user = make_user(db, email="sacreate2@univ.br", role="superadmin")
        token = make_token(user)
        resp = client.post(
            "/api/institutions/",
            json={"email": "admin@newgroup.br"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 201

    def test_rejects_public_email(self, client, db):
        user = make_user(db, email="sapublic@univ.br", role="superadmin")
        token = make_token(user)
        resp = client.post(
            "/api/institutions/",
            json={"email": "test@gmail.com"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 422

    def test_professor_cannot_create(self, client, db):
        _, user = make_professor_user(db, "Prof No Create", "profnocreate@univ.br")
        token = make_token(user)
        resp = client.post(
            "/api/institutions/",
            json={"email": "admin@someinst.br"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 403


class TestListMyEmails:
    def test_professor_lists_own_emails(self, client, db):
        prof, user = make_professor_user(db, "Prof Email List", "profemail@univ.br")
        institution_service.add_institutional_email(db, prof, "profemail@someinst.br")
        token = make_token(user)
        resp = client.get("/api/institutions/my-emails", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)
        assert len(resp.json()) == 1

    def test_returns_empty_when_no_emails(self, client, db):
        _, user = make_professor_user(db, "Prof No Emails", "profnoemails@univ.br")
        token = make_token(user)
        resp = client.get("/api/institutions/my-emails", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        assert resp.json() == []


class TestAddMyEmail:
    def test_adds_email(self, client, db):
        prof, user = make_professor_user(db, "Prof Add Email", "profaddemail@univ.br")
        token = make_token(user)
        resp = client.post(
            "/api/institutions/my-emails",
            json={"email": "profadd@addinst.br"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 201
        assert resp.json()["institutional_email"] == "profadd@addinst.br"

    def test_rejects_public_email(self, client, db):
        _, user = make_professor_user(db, "Prof Public Email", "profpublic@univ.br")
        token = make_token(user)
        resp = client.post(
            "/api/institutions/my-emails",
            json={"email": "prof@hotmail.com"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 422

    def test_rejects_duplicate_institution(self, client, db):
        prof, user = make_professor_user(db, "Prof Dup Email", "profdupemail@univ.br")
        institution_service.add_institutional_email(db, prof, "dup@dupinst.br")
        token = make_token(user)
        resp = client.post(
            "/api/institutions/my-emails",
            json={"email": "dup2@dupinst.br"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code in (409, 422)


class TestRemoveMyEmail:
    def test_removes_email(self, client, db):
        prof, user = make_professor_user(db, "Prof Remove Email", "profrm@univ.br")
        pi1 = institution_service.add_institutional_email(db, prof, "rm1@rminst.br")
        pi2 = institution_service.add_institutional_email(db, prof, "rm2@rminst2.br")
        token = make_token(user)
        resp = client.delete(f"/api/institutions/my-emails/{pi2.id}", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 204

    def test_cannot_remove_last_email(self, client, db):
        prof, user = make_professor_user(db, "Prof Last Email", "proflast@univ.br")
        pi = institution_service.add_institutional_email(db, prof, "last@lastinst.br")
        token = make_token(user)
        resp = client.delete(f"/api/institutions/my-emails/{pi.id}", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 400

    def test_returns_400_for_not_found(self, client, db):
        prof, user = make_professor_user(db, "Prof NF Email", "profnfemail@univ.br")
        institution_service.add_institutional_email(db, prof, "nf1@nfinst.br")
        institution_service.add_institutional_email(db, prof, "nf2@nfinst2.br")
        token = make_token(user)
        resp = client.delete("/api/institutions/my-emails/9999", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 400

"""Tests for app/routers/users.py"""
from app.routers.auth import make_token

from .conftest import make_user


class TestUpdateMyProfile:
    def test_updates_bio(self, client, db):
        user = make_user(db, email="mybio@univ.br", role="researcher")
        token = make_token(user)
        resp = client.patch(
            "/api/users/me",
            json={"bio": "Minha bio"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["bio"] == "Minha bio"

    def test_requires_auth(self, client, db):
        resp = client.patch("/api/users/me", json={"bio": "X"})
        assert resp.status_code in (401, 403)

    def test_updates_lattes_url(self, client, db):
        user = make_user(db, email="mylattes@univ.br", role="researcher")
        token = make_token(user)
        resp = client.patch(
            "/api/users/me",
            json={"lattes_url": "http://lattes.cnpq.br/1234567890123456"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["lattes_url"] == "http://lattes.cnpq.br/1234567890123456"

    def test_updates_interesses(self, client, db):
        user = make_user(db, email="mypatch@univ.br", role="researcher")
        token = make_token(user)
        resp = client.patch(
            "/api/users/me",
            json={"interesses": "Machine Learning, NLP"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["interesses"] == "Machine Learning, NLP"


class TestUpdateUserProfile:
    def test_professor_updates_any_user(self, client, db):
        prof = make_user(db, email="profpatch@univ.br", role="professor")
        target = make_user(db, email="targetpatch@univ.br", role="researcher")
        token = make_token(prof)
        resp = client.patch(
            f"/api/users/{target.id}",
            json={"bio": "Bio nova"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["bio"] == "Bio nova"

    def test_user_updates_own_profile(self, client, db):
        user = make_user(db, email="selfpatch@univ.br", role="researcher")
        token = make_token(user)
        resp = client.patch(
            f"/api/users/{user.id}",
            json={"bio": "Bio Propria"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["bio"] == "Bio Propria"

    def test_researcher_cannot_update_other(self, client, db):
        user1 = make_user(db, email="r1patch@univ.br", role="researcher")
        user2 = make_user(db, email="r2patch@univ.br", role="researcher")
        token = make_token(user1)
        resp = client.patch(
            f"/api/users/{user2.id}",
            json={"bio": "Tentativa"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 403

    def test_returns_404_for_unknown(self, client, db):
        prof = make_user(db, email="prof404p@univ.br", role="professor")
        token = make_token(prof)
        resp = client.patch(
            "/api/users/9999",
            json={"bio": "x"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 404

    def test_superadmin_updates_any_user(self, client, db):
        admin = make_user(db, email="sa_users@univ.br", role="superadmin")
        target = make_user(db, email="sa_target@univ.br", role="researcher")
        token = make_token(admin)
        resp = client.patch(
            f"/api/users/{target.id}",
            json={"bio": "Admin set bio"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["bio"] == "Admin set bio"

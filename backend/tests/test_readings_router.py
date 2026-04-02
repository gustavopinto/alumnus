"""Tests for app/routers/readings.py"""
import pytest
from unittest.mock import patch

from app.routers.auth import make_token

from .conftest import make_user, make_researcher

URL = "https://example.com/paper"


def _auth(client, db, role="professor"):
    user = make_user(db, email=f"{role}_rd@univ.br", role=role)
    return {"Authorization": f"Bearer {make_token(user)}"}


def _researcher_token(db, researcher):
    return {"Authorization": f"Bearer {make_token(researcher.user)}"}


@pytest.fixture(autouse=True)
def no_bg_fetch():
    with patch("app.services.reading_service.fetch_and_set_title"):
        yield


class TestListReadings:
    def test_empty(self, client, db):
        r = make_researcher(db, nome="R List", email="r_list_rd@u.br")
        resp = client.get(f"/api/users/{r.user.id}/readings/", headers=_auth(client, db))
        assert resp.status_code == 200
        assert resp.json() == []

    def test_returns_created(self, client, db):
        r = make_researcher(db, nome="R List2", email="r_list2_rd@u.br")
        headers = _auth(client, db, "professor")
        client.post(f"/api/users/{r.user.id}/readings/", json={"url": URL}, headers=headers)
        resp = client.get(f"/api/users/{r.user.id}/readings/", headers=headers)
        data = resp.json()
        assert len(data) == 1
        assert data[0]["url"] == URL
        assert data[0]["status"] == "quero_ler"

    def test_404_unknown_user(self, client, db):
        resp = client.get("/api/users/9999/readings/", headers=_auth(client, db))
        assert resp.status_code == 404


class TestCreateReading:
    def test_professor_can_create(self, client, db):
        r = make_researcher(db, nome="R Create", email="r_create_rd@u.br")
        resp = client.post(
            f"/api/users/{r.user.id}/readings/",
            json={"url": URL},
            headers=_auth(client, db),
        )
        assert resp.status_code == 201
        assert resp.json()["url"] == URL
        assert resp.json()["user_id"] == r.user.id
        assert resp.json()["status"] == "quero_ler"
        assert len(resp.json()["status_history"]) == 1

    def test_own_researcher_can_create(self, client, db):
        r = make_researcher(db, nome="R Own", email="r_own_rd@u.br", password="pass")
        headers = _researcher_token(db, r)
        resp = client.post(f"/api/users/{r.user.id}/readings/", json={"url": URL}, headers=headers)
        assert resp.status_code == 201

    def test_other_researcher_cannot_create(self, client, db):
        r1 = make_researcher(db, nome="R1", email="r1_rd@u.br", password="pass")
        r2 = make_researcher(db, nome="R2", email="r2_rd@u.br")
        headers = _researcher_token(db, r1)
        resp = client.post(f"/api/users/{r2.user.id}/readings/", json={"url": URL}, headers=headers)
        assert resp.status_code == 403

    def test_missing_url_returns_422(self, client, db):
        r = make_researcher(db, nome="R Bad", email="r_bad_rd@u.br")
        resp = client.post(
            f"/api/users/{r.user.id}/readings/",
            json={"url": ""},
            headers=_auth(client, db),
        )
        assert resp.status_code == 422

    def test_duplicate_url_returns_409(self, client, db):
        r = make_researcher(db, nome="R Dup", email="r_dup_rd@u.br")
        headers = _auth(client, db)
        client.post(f"/api/users/{r.user.id}/readings/", json={"url": URL}, headers=headers)
        resp = client.post(f"/api/users/{r.user.id}/readings/", json={"url": URL}, headers=headers)
        assert resp.status_code == 409


class TestUpdateStatus:
    def test_professor_can_update_status(self, client, db):
        r = make_researcher(db, nome="R Upd", email="r_upd_rd@u.br")
        headers = _auth(client, db)
        created = client.post(f"/api/users/{r.user.id}/readings/", json={"url": URL}, headers=headers).json()
        resp = client.patch(
            f"/api/users/{r.user.id}/readings/{created['id']}",
            json={"status": "lendo"},
            headers=headers,
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "lendo"
        assert len(resp.json()["status_history"]) == 2

    def test_invalid_status_returns_422(self, client, db):
        r = make_researcher(db, nome="R Bad St", email="r_bad_st_rd@u.br")
        headers = _auth(client, db)
        created = client.post(f"/api/users/{r.user.id}/readings/", json={"url": URL}, headers=headers).json()
        resp = client.patch(
            f"/api/users/{r.user.id}/readings/{created['id']}",
            json={"status": "invalido"},
            headers=headers,
        )
        assert resp.status_code == 422

    def test_404_unknown_reading(self, client, db):
        r = make_researcher(db, nome="R 404", email="r_404_rd@u.br")
        resp = client.patch(
            f"/api/users/{r.user.id}/readings/9999",
            json={"status": "lendo"},
            headers=_auth(client, db),
        )
        assert resp.status_code == 404


class TestDeleteReading:
    def test_professor_can_delete(self, client, db):
        r = make_researcher(db, nome="R Del", email="r_del_rd@u.br")
        headers = _auth(client, db)
        created = client.post(f"/api/users/{r.user.id}/readings/", json={"url": URL}, headers=headers).json()
        resp = client.delete(f"/api/users/{r.user.id}/readings/{created['id']}", headers=headers)
        assert resp.status_code == 204
        remaining = client.get(f"/api/users/{r.user.id}/readings/", headers=headers).json()
        assert remaining == []

    def test_other_researcher_cannot_delete(self, client, db):
        r1 = make_researcher(db, nome="R1 Del", email="r1_del_rd@u.br", password="pass")
        r2 = make_researcher(db, nome="R2 Del", email="r2_del_rd@u.br")
        prof_headers = _auth(client, db)
        created = client.post(f"/api/users/{r2.user.id}/readings/", json={"url": URL}, headers=prof_headers).json()
        r1_headers = _researcher_token(db, r1)
        resp = client.delete(f"/api/users/{r2.user.id}/readings/{created['id']}", headers=r1_headers)
        assert resp.status_code == 403

"""Tests for app/routers/milestones.py"""
import pytest
from app.routers.auth import make_token

from .conftest import make_user, make_researcher


def _auth(client, db, role="professor"):
    user = make_user(db, email=f"{role}_ms@univ.br", role=role)
    return {"Authorization": f"Bearer {make_token(user)}"}


def _researcher_token(db, researcher):
    return {"Authorization": f"Bearer {make_token(researcher.user)}"}


PAYLOAD = {"type": "publicacao", "title": "Artigo A", "date": "2024-06-01"}


class TestListMilestones:
    def test_empty(self, client, db):
        r = make_researcher(db, nome="R List", email="r_list_ms@u.br")
        resp = client.get(f"/api/users/{r.user.id}/milestones/", headers=_auth(client, db))
        assert resp.status_code == 200
        assert resp.json() == []

    def test_returns_created(self, client, db):
        r = make_researcher(db, nome="R List2", email="r_list2_ms@u.br")
        headers = _auth(client, db, "professor")
        client.post(f"/api/users/{r.user.id}/milestones/", json=PAYLOAD, headers=headers)
        resp = client.get(f"/api/users/{r.user.id}/milestones/", headers=headers)
        assert len(resp.json()) == 1
        assert resp.json()[0]["title"] == "Artigo A"

    def test_404_unknown_user(self, client, db):
        resp = client.get("/api/users/9999/milestones/", headers=_auth(client, db))
        assert resp.status_code == 404


class TestCreateMilestone:
    def test_professor_can_create(self, client, db):
        r = make_researcher(db, nome="R Create", email="r_create_ms@u.br")
        resp = client.post(f"/api/users/{r.user.id}/milestones/", json=PAYLOAD, headers=_auth(client, db))
        assert resp.status_code == 201
        assert resp.json()["type"] == "publicacao"
        assert resp.json()["user_id"] == r.user.id

    def test_own_researcher_can_create(self, client, db):
        r = make_researcher(db, nome="R Own", email="r_own_ms@u.br", password="pass")
        headers = _researcher_token(db, r)
        resp = client.post(f"/api/users/{r.user.id}/milestones/", json=PAYLOAD, headers=headers)
        assert resp.status_code == 201

    def test_other_researcher_cannot_create(self, client, db):
        r1 = make_researcher(db, nome="R1 Other", email="r1_other_ms@u.br", password="pass")
        r2 = make_researcher(db, nome="R2 Other", email="r2_other_ms@u.br")
        headers = _researcher_token(db, r1)
        resp = client.post(f"/api/users/{r2.user.id}/milestones/", json=PAYLOAD, headers=headers)
        assert resp.status_code == 403

    def test_invalid_type_returns_422(self, client, db):
        r = make_researcher(db, nome="R Invalid", email="r_invalid_ms@u.br")
        resp = client.post(
            f"/api/users/{r.user.id}/milestones/",
            json={**PAYLOAD, "type": "invalido"},
            headers=_auth(client, db),
        )
        assert resp.status_code == 422


class TestUpdateMilestone:
    def test_professor_can_update(self, client, db):
        r = make_researcher(db, nome="R Upd", email="r_upd_ms@u.br")
        headers = _auth(client, db)
        created = client.post(f"/api/users/{r.user.id}/milestones/", json=PAYLOAD, headers=headers).json()
        resp = client.put(
            f"/api/users/{r.user.id}/milestones/{created['id']}",
            json={"title": "Artigo Atualizado"},
            headers=headers,
        )
        assert resp.status_code == 200
        assert resp.json()["title"] == "Artigo Atualizado"

    def test_404_unknown_milestone(self, client, db):
        r = make_researcher(db, nome="R 404 Upd", email="r_404_upd_ms@u.br")
        resp = client.put(
            f"/api/users/{r.user.id}/milestones/9999",
            json={"title": "X"},
            headers=_auth(client, db),
        )
        assert resp.status_code == 404


class TestDeleteMilestone:
    def test_professor_can_delete(self, client, db):
        r = make_researcher(db, nome="R Del", email="r_del_ms@u.br")
        headers = _auth(client, db)
        created = client.post(f"/api/users/{r.user.id}/milestones/", json=PAYLOAD, headers=headers).json()
        resp = client.delete(f"/api/users/{r.user.id}/milestones/{created['id']}", headers=headers)
        assert resp.status_code == 204
        remaining = client.get(f"/api/users/{r.user.id}/milestones/", headers=headers).json()
        assert remaining == []

    def test_other_researcher_cannot_delete(self, client, db):
        r1 = make_researcher(db, nome="R1 Del", email="r1_del_ms@u.br", password="pass")
        r2 = make_researcher(db, nome="R2 Del", email="r2_del_ms@u.br")
        prof_headers = _auth(client, db)
        created = client.post(f"/api/users/{r2.user.id}/milestones/", json=PAYLOAD, headers=prof_headers).json()
        r1_headers = _researcher_token(db, r1)
        resp = client.delete(f"/api/users/{r2.user.id}/milestones/{created['id']}", headers=r1_headers)
        assert resp.status_code == 403

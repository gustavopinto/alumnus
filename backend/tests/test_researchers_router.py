"""Tests for app/routers/researchers.py"""
from app.routers.auth import make_token
from app.schemas import ResearcherCreate
from app.services import researcher_service

from .conftest import make_user


class TestListResearchers:
    def test_list_researchers_empty(self, client, db):
        resp = client.get("/api/researchers/")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_list_researchers_with_data(self, client, db):
        researcher_service.create(db, ResearcherCreate(email="listrouter@univ.br", nome="List Router", status="mestrado"))
        resp = client.get("/api/researchers/")
        assert len(resp.json()) >= 1

    def test_filter_active(self, client, db):
        resp = client.get("/api/researchers/?ativo=true")
        assert resp.status_code == 200

    def test_filter_inactive(self, client, db):
        r = researcher_service.create(db, ResearcherCreate(email="inactive_router@univ.br", nome="Inactive Router", status="mestrado"))
        researcher_service.deactivate(db, r)
        resp = client.get("/api/researchers/?ativo=false")
        assert resp.status_code == 200
        ids = [item["id"] for item in resp.json()]
        assert r.id in ids


class TestCreateResearcher:
    def test_creates_researcher(self, client, db):
        resp = client.post("/api/researchers/", json={
            "email": "new_r@univ.br",
            "nome": "New Researcher",
            "status": "mestrado",
        })
        assert resp.status_code == 201
        assert resp.json()["status"] == "mestrado"
        assert resp.json()["id"] is not None

    def test_duplicate_email_returns_409(self, client, db):
        client.post("/api/researchers/", json={"email": "dup_router@univ.br", "nome": "Dup", "status": "mestrado"})
        resp = client.post("/api/researchers/", json={"email": "dup_router@univ.br", "nome": "Dup2", "status": "doutorado"})
        assert resp.status_code == 409


class TestGetResearcherById:
    def test_get_by_id(self, client, db):
        r = researcher_service.create(db, ResearcherCreate(email="getid_router@univ.br", nome="GetId Router", status="mestrado"))
        resp = client.get(f"/api/researchers/{r.id}")
        assert resp.status_code == 200
        assert resp.json()["id"] == r.id

    def test_returns_404_for_unknown(self, client, db):
        resp = client.get("/api/researchers/9999")
        assert resp.status_code == 404


class TestGetResearcherBySlug:
    def test_get_by_slug(self, client, db):
        researcher_service.create(db, ResearcherCreate(email="slug_router@univ.br", nome="Fulano Slug Router", status="mestrado"))
        resp = client.get("/api/researchers/by-slug/fulano-slug-router")
        assert resp.status_code == 200

    def test_get_by_slug_404(self, client, db):
        resp = client.get("/api/researchers/by-slug/nao-existe-xyz-router")
        assert resp.status_code == 404


class TestGetResearcherUser:
    def test_get_linked_user(self, client, db):
        r = researcher_service.create(db, ResearcherCreate(email="linked_router@univ.br", nome="Linked Router", status="mestrado"))
        resp = client.get(f"/api/researchers/{r.id}/user")
        assert resp.status_code == 200


class TestUpdateResearcher:
    def test_professor_can_update_any(self, client, db):
        r = researcher_service.create(db, ResearcherCreate(email="upd_router@univ.br", nome="Upd Router", status="mestrado"))
        user = make_user(db, email="prof_upd_router@univ.br", role="professor")
        token = make_token(user)
        resp = client.put(
            f"/api/researchers/{r.id}",
            json={"status": "doutorado"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "doutorado"

    def test_researcher_can_update_own(self, client, db):
        r = researcher_service.create(db, ResearcherCreate(email="self_upd@univ.br", nome="Self Upd", status="mestrado"))
        # Get the linked user created by the service
        user = researcher_service.get_linked_user(db, r.id)
        token = make_token(user)
        resp = client.put(
            f"/api/researchers/{r.id}",
            json={"status": "doutorado"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200

    def test_returns_404_for_unknown(self, client, db):
        user = make_user(db, email="p403_router@univ.br", role="professor")
        token = make_token(user)
        resp = client.put(
            "/api/researchers/9999",
            json={"status": "doutorado"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 404

    def test_researcher_cannot_update_other(self, client, db):
        r1 = researcher_service.create(db, ResearcherCreate(email="r1other@univ.br", nome="R1 Other", status="mestrado"))
        r2 = researcher_service.create(db, ResearcherCreate(email="r2other@univ.br", nome="R2 Other", status="mestrado"))
        user = researcher_service.get_linked_user(db, r1.id)
        token = make_token(user)
        resp = client.put(
            f"/api/researchers/{r2.id}",
            json={"status": "doutorado"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 403


class TestDeactivateResearcher:
    def test_deactivates(self, client, db):
        r = researcher_service.create(db, ResearcherCreate(email="deact_router@univ.br", nome="Deact Router", status="mestrado"))
        resp = client.delete(f"/api/researchers/{r.id}")
        assert resp.status_code == 204

    def test_returns_404_for_unknown(self, client, db):
        resp = client.delete("/api/researchers/9999")
        assert resp.status_code == 404

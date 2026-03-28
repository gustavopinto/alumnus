"""Tests for app/routers/relationships.py"""
from app.schemas import ResearcherCreate
from app.services import researcher_service


def make_researcher(db, email, nome):
    return researcher_service.create(db, ResearcherCreate(email=email, nome=nome, status="mestrado"))


class TestListRelationships:
    def test_list_empty(self, client, db):
        resp = client.get("/api/relationships/")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_list_after_create(self, client, db):
        r1 = make_researcher(db, "listrel1@test.br", "List Rel 1")
        r2 = make_researcher(db, "listrel2@test.br", "List Rel 2")
        client.post("/api/relationships/", json={
            "source_researcher_id": r1.id,
            "target_researcher_id": r2.id,
            "relation_type": "colaboracao",
        })
        resp = client.get("/api/relationships/")
        assert len(resp.json()) == 1


class TestCreateRelationship:
    def test_creates_relationship(self, client, db):
        r1 = make_researcher(db, "relr1@test.br", "Rel Router 1")
        r2 = make_researcher(db, "relr2@test.br", "Rel Router 2")
        resp = client.post("/api/relationships/", json={
            "source_researcher_id": r1.id,
            "target_researcher_id": r2.id,
            "relation_type": "colaboracao",
        })
        assert resp.status_code == 201
        data = resp.json()
        assert data["source_researcher_id"] == r1.id
        assert data["target_researcher_id"] == r2.id
        assert data["relation_type"] == "colaboracao"


class TestUpdateRelationship:
    def test_updates_relationship(self, client, db):
        r1 = make_researcher(db, "updr1@test.br", "Upd Router 1")
        r2 = make_researcher(db, "updr2@test.br", "Upd Router 2")
        create_resp = client.post("/api/relationships/", json={
            "source_researcher_id": r1.id,
            "target_researcher_id": r2.id,
            "relation_type": "old_type",
        })
        rel_id = create_resp.json()["id"]
        update_resp = client.put(f"/api/relationships/{rel_id}", json={"relation_type": "new_type"})
        assert update_resp.status_code == 200
        assert update_resp.json()["relation_type"] == "new_type"

    def test_returns_404_for_unknown(self, client, db):
        resp = client.put("/api/relationships/9999", json={"relation_type": "x"})
        assert resp.status_code == 404


class TestDeleteRelationship:
    def test_deletes_relationship(self, client, db):
        r1 = make_researcher(db, "delrr1@test.br", "Del Router 1")
        r2 = make_researcher(db, "delrr2@test.br", "Del Router 2")
        create_resp = client.post("/api/relationships/", json={
            "source_researcher_id": r1.id,
            "target_researcher_id": r2.id,
            "relation_type": "temp",
        })
        rel_id = create_resp.json()["id"]
        del_resp = client.delete(f"/api/relationships/{rel_id}")
        assert del_resp.status_code == 204
        # confirm gone
        list_resp = client.get("/api/relationships/")
        assert all(r["id"] != rel_id for r in list_resp.json())

    def test_returns_404_for_unknown(self, client, db):
        resp = client.delete("/api/relationships/9999")
        assert resp.status_code == 404

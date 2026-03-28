"""Tests for app/routers/graph.py"""
from app.schemas import ResearcherCreate
from app.services import researcher_service


class TestGetGraph:
    def test_returns_graph_structure(self, client, db):
        resp = client.get("/api/graph/")
        assert resp.status_code == 200
        data = resp.json()
        assert "nodes" in data
        assert "edges" in data

    def test_includes_researchers_in_nodes(self, client, db):
        r = researcher_service.create(db, ResearcherCreate(email="graphrouter@test.br", nome="Graph Router R", status="mestrado"))
        resp = client.get("/api/graph/")
        assert resp.status_code == 200
        node_ids = [n["id"] for n in resp.json()["nodes"]]
        assert str(r.id) in node_ids

    def test_with_institution_id_filter(self, client, db):
        resp = client.get("/api/graph/?institution_id=999")
        assert resp.status_code == 200
        data = resp.json()
        assert "nodes" in data
        assert "edges" in data

    def test_empty_graph_when_no_data(self, client, db):
        resp = client.get("/api/graph/")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data["nodes"], list)
        assert isinstance(data["edges"], list)


class TestUpdateLayout:
    def test_updates_layout(self, client, db):
        resp = client.put("/api/graph/layout", json={"positions": {"p1": {"x": 100, "y": 200}}})
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert "p1" in data["positions"]
        assert data["positions"]["p1"] == {"x": 100, "y": 200}

    def test_merges_layout(self, client, db):
        client.put("/api/graph/layout", json={"positions": {"p1": {"x": 10, "y": 20}}})
        resp = client.put("/api/graph/layout", json={"positions": {"p2": {"x": 30, "y": 40}}})
        assert resp.status_code == 200
        positions = resp.json()["positions"]
        assert "p1" in positions
        assert "p2" in positions

    def test_empty_positions(self, client, db):
        resp = client.put("/api/graph/layout", json={"positions": {}})
        assert resp.status_code == 200

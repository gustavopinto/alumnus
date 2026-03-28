"""Tests for app/services/graph_service.py"""
import pytest
from passlib.context import CryptContext

from app.models import GraphLayout, Institution, Professor, ProfessorInstitution, ResearchGroup, User
from app.schemas import LayoutUpdate, ResearcherCreate
from app.services import graph_service, researcher_service

pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")


def make_professor(db, nome="Prof Graph", email="prof@graph.br"):
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
    return prof


class TestBuildGraphPayload:
    def test_returns_nodes_and_edges_keys(self, db):
        result = graph_service.build_graph_payload(db)
        assert "nodes" in result
        assert "edges" in result
        assert isinstance(result["nodes"], list)
        assert isinstance(result["edges"], list)

    def test_includes_professor_node(self, db):
        prof = make_professor(db)
        result = graph_service.build_graph_payload(db)
        node_ids = [n["id"] for n in result["nodes"]]
        assert f"p{prof.id}" in node_ids

    def test_professor_node_has_correct_data(self, db):
        prof = make_professor(db, "Prof Node Data", "nodedata@graph.br")
        result = graph_service.build_graph_payload(db)
        node = next(n for n in result["nodes"] if n["id"] == f"p{prof.id}")
        assert node["data"]["status"] == "professor"
        assert node["data"]["name"] == "Prof Node Data"

    def test_includes_researcher_node(self, db):
        r = researcher_service.create(db, ResearcherCreate(email="graphr@graph.br", nome="Graph Researcher", status="mestrado"))
        result = graph_service.build_graph_payload(db)
        node_ids = [n["id"] for n in result["nodes"]]
        assert str(r.id) in node_ids

    def test_researcher_node_has_status_color(self, db):
        r = researcher_service.create(db, ResearcherCreate(email="colorr@graph.br", nome="Color Researcher", status="doutorado"))
        result = graph_service.build_graph_payload(db)
        node = next(n for n in result["nodes"] if n["id"] == str(r.id))
        assert node["data"]["color"] == "#10B981"

    def test_includes_advisor_edge(self, db):
        prof = make_professor(db, "Prof Advisor", "advisor@graph.br")
        r = researcher_service.create(db, ResearcherCreate(
            email="advedger@graph.br",
            nome="Advised Researcher",
            status="mestrado",
            orientador_id=prof.id,
        ))
        result = graph_service.build_graph_payload(db)
        edge_ids = [e["id"] for e in result["edges"]]
        assert f"orient-{r.id}" in edge_ids

    def test_inactive_professor_excluded(self, db):
        prof = make_professor(db, "Prof Inactive Graph", "inactive@graph.br")
        prof.ativo = False
        db.commit()
        result = graph_service.build_graph_payload(db)
        node_ids = [n["id"] for n in result["nodes"]]
        assert f"p{prof.id}" not in node_ids

    def test_inactive_researcher_excluded(self, db):
        r = researcher_service.create(db, ResearcherCreate(email="inactiver@graph.br", nome="Inactive Researcher Graph", status="mestrado"))
        researcher_service.deactivate(db, r)
        result = graph_service.build_graph_payload(db)
        node_ids = [n["id"] for n in result["nodes"]]
        assert str(r.id) not in node_ids

    def test_filters_by_institution(self, db):
        inst = Institution(name="GRAPH_INST", domain="graphinst.br")
        db.add(inst)
        db.flush()
        prof = make_professor(db, "Prof Graph Inst", "pinst@graphinst.br")
        pi = ProfessorInstitution(professor_id=prof.id, institution_id=inst.id, institutional_email="pinst@graphinst.br")
        db.add(pi)
        db.commit()

        # Professor in other institution
        other_prof = make_professor(db, "Prof Other Inst", "pother@other.br")

        result = graph_service.build_graph_payload(db, institution_id=inst.id)
        node_ids = [n["id"] for n in result["nodes"]]
        assert f"p{prof.id}" in node_ids
        assert f"p{other_prof.id}" not in node_ids

    def test_uses_saved_layout_positions(self, db):
        prof = make_professor(db, "Prof Layout", "layout@graph.br")
        node_id = f"p{prof.id}"
        layout = GraphLayout(name="default", layout_jsonb={node_id: {"x": 999, "y": 888}})
        db.add(layout)
        db.commit()

        result = graph_service.build_graph_payload(db)
        node = next(n for n in result["nodes"] if n["id"] == node_id)
        assert node["position"]["x"] == 999
        assert node["position"]["y"] == 888


class TestMergeLayout:
    def test_creates_layout_if_not_exists(self, db):
        data = LayoutUpdate(positions={"p1": {"x": 100, "y": 200}})
        result = graph_service.merge_layout(db, data)
        assert result["p1"] == {"x": 100, "y": 200}

    def test_merges_with_existing_layout(self, db):
        graph_service.merge_layout(db, LayoutUpdate(positions={"p1": {"x": 10, "y": 20}}))
        result = graph_service.merge_layout(db, LayoutUpdate(positions={"p2": {"x": 30, "y": 40}}))
        assert "p1" in result
        assert "p2" in result

    def test_overwrites_existing_position(self, db):
        graph_service.merge_layout(db, LayoutUpdate(positions={"p1": {"x": 10, "y": 20}}))
        result = graph_service.merge_layout(db, LayoutUpdate(positions={"p1": {"x": 99, "y": 88}}))
        assert result["p1"] == {"x": 99, "y": 88}

    def test_persists_to_database(self, db):
        graph_service.merge_layout(db, LayoutUpdate(positions={"saved": {"x": 1, "y": 2}}))
        layout = db.query(GraphLayout).filter_by(name="default").first()
        assert layout is not None
        assert "saved" in layout.layout_jsonb

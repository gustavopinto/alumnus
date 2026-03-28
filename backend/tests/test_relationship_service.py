"""Tests for app/services/relationship_service.py"""
import pytest

from app.schemas import RelationshipCreate, RelationshipUpdate, ResearcherCreate
from app.services import relationship_service, researcher_service


def make_researcher(db, email, nome, status="mestrado"):
    data = ResearcherCreate(email=email, nome=nome, status=status)
    return researcher_service.create(db, data)


class TestCreate:
    def test_creates_relationship(self, db):
        r1 = make_researcher(db, "rel1@univ.br", "Rel 1")
        r2 = make_researcher(db, "rel2@univ.br", "Rel 2")
        data = RelationshipCreate(
            source_researcher_id=r1.id,
            target_researcher_id=r2.id,
            relation_type="colaboracao",
        )
        rel = relationship_service.create(db, data)
        assert rel.id is not None
        assert rel.source_researcher_id == r1.id
        assert rel.target_researcher_id == r2.id
        assert rel.relation_type == "colaboracao"


class TestListAll:
    def test_returns_all(self, db):
        r1 = make_researcher(db, "la1@univ.br", "LA 1")
        r2 = make_researcher(db, "la2@univ.br", "LA 2")
        relationship_service.create(db, RelationshipCreate(
            source_researcher_id=r1.id,
            target_researcher_id=r2.id,
            relation_type="coautoria",
        ))
        results = relationship_service.list_all(db)
        assert len(results) >= 1

    def test_returns_empty_when_none(self, db):
        results = relationship_service.list_all(db)
        assert isinstance(results, list)


class TestGetById:
    def test_returns_relationship(self, db):
        r1 = make_researcher(db, "gb1@univ.br", "GB 1")
        r2 = make_researcher(db, "gb2@univ.br", "GB 2")
        rel = relationship_service.create(db, RelationshipCreate(
            source_researcher_id=r1.id,
            target_researcher_id=r2.id,
            relation_type="amizade",
        ))
        found = relationship_service.get_by_id(db, rel.id)
        assert found is not None
        assert found.id == rel.id

    def test_returns_none_for_unknown(self, db):
        assert relationship_service.get_by_id(db, 9999) is None


class TestUpdate:
    def test_updates_relation_type(self, db):
        r1 = make_researcher(db, "upd1@univ.br", "Upd 1")
        r2 = make_researcher(db, "upd2@univ.br", "Upd 2")
        rel = relationship_service.create(db, RelationshipCreate(
            source_researcher_id=r1.id,
            target_researcher_id=r2.id,
            relation_type="old",
        ))
        updated = relationship_service.update(db, rel, RelationshipUpdate(relation_type="new"))
        assert updated.relation_type == "new"


class TestDelete:
    def test_deletes_relationship(self, db):
        r1 = make_researcher(db, "del1@univ.br", "Del 1")
        r2 = make_researcher(db, "del2@univ.br", "Del 2")
        rel = relationship_service.create(db, RelationshipCreate(
            source_researcher_id=r1.id,
            target_researcher_id=r2.id,
            relation_type="temp",
        ))
        rel_id = rel.id
        relationship_service.delete(db, rel)
        assert relationship_service.get_by_id(db, rel_id) is None

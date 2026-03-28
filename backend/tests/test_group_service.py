"""Tests for app/services/group_service.py"""
import pytest
from passlib.context import CryptContext

from app.models import Institution, Professor, ProfessorGroup, ProfessorInstitution, ResearchGroup, User
from app.services import group_service

pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")


def make_institution(db, name="UNICAMP", domain="unicamp.br"):
    inst = Institution(name=name, domain=domain)
    db.add(inst)
    db.commit()
    db.refresh(inst)
    return inst


def make_professor(db, nome="Prof Teste", email=None):
    if email is None:
        email = f"prof_{nome.lower().replace(' ', '_')}@inst.br"
    prof = Professor()
    db.add(prof)
    db.flush()
    user = User(
        email=email,
        nome=nome,
        password_hash=pwd_ctx.hash("testpass"),
        role="professor",
        professor_id=prof.id,
    )
    db.add(user)
    db.commit()
    db.refresh(prof)
    return prof


def link_professor_institution(db, professor, institution, email=None):
    if email is None:
        email = f"prof{professor.id}@{institution.domain}"
    pi = ProfessorInstitution(
        professor_id=professor.id,
        institution_id=institution.id,
        institutional_email=email,
    )
    db.add(pi)
    db.commit()
    db.refresh(pi)
    return pi


class TestListProfessorGroups:
    def test_empty_when_no_groups(self, db):
        prof = make_professor(db, "Prof Sem Grupos", "semgrupos@inst.br")
        result = group_service.list_professor_groups(db, prof)
        assert result == []

    def test_returns_groups(self, db):
        inst = make_institution(db, "UFMG", "ufmg.br")
        prof = make_professor(db, "Prof Com Grupos", "comgrupos@ufmg.br")
        group = group_service.create_group(db, prof, "Grupo A", inst.id)
        result = group_service.list_professor_groups(db, prof)
        assert len(result) == 1
        assert result[0].id == group.id


class TestGetCoordinatorGroup:
    def test_returns_none_when_no_group(self, db):
        prof = make_professor(db, "Prof Sem Coord", "semcoord@inst.br")
        result = group_service.get_coordinator_group(db, prof)
        assert result is None

    def test_returns_coordinator_group(self, db):
        inst = make_institution(db, "USP", "usp.br")
        prof = make_professor(db, "Prof Coord", "profcoord@usp.br")
        group = group_service.create_group(db, prof, "Grupo USP", inst.id)
        result = group_service.get_coordinator_group(db, prof)
        assert result is not None
        assert result.id == group.id


class TestCreateGroup:
    def test_creates_group_and_professor_group(self, db):
        inst = make_institution(db, "UFRJ", "ufrj.br")
        prof = make_professor(db, "Prof UFRJ", "prof@ufrj.br")
        group = group_service.create_group(db, prof, "Grupo UFRJ", inst.id)
        assert group.id is not None
        assert group.name == "Grupo UFRJ"
        assert group.institution_id == inst.id
        pg = db.query(ProfessorGroup).filter_by(professor_id=prof.id, group_id=group.id).first()
        assert pg is not None
        assert pg.role_in_group == "coordinator"


class TestCreateGroupDirect:
    def test_creates_group_without_professor(self, db):
        inst = make_institution(db, "PUC", "puc.br")
        group = group_service.create_group_direct(db, "Grupo PUC", inst.id)
        assert group.id is not None
        assert group.name == "Grupo PUC"


class TestJoinGroup:
    def test_professor_joins_group(self, db):
        inst = make_institution(db, "UFSC", "ufsc.br")
        prof1 = make_professor(db, "Prof Coord UFSC", "coord@ufsc.br")
        group = group_service.create_group(db, prof1, "Grupo UFSC", inst.id)

        prof2 = make_professor(db, "Prof Member UFSC", "member@ufsc.br")
        link_professor_institution(db, prof2, inst)

        pg = group_service.join_group(db, prof2, group.id, inst.id)
        assert pg.role_in_group == "member"

    def test_raises_when_no_institution_link(self, db):
        inst = make_institution(db, "UFBA", "ufba.br")
        prof1 = make_professor(db, "Prof Coord UFBA", "coord@ufba.br")
        group = group_service.create_group(db, prof1, "Grupo UFBA", inst.id)

        prof2 = make_professor(db, "Prof Sem Vinculo", "semvinculo@other.br")
        with pytest.raises(ValueError, match="sem_vinculo_instituicao"):
            group_service.join_group(db, prof2, group.id, inst.id)

    def test_raises_when_already_member(self, db):
        inst = make_institution(db, "UNIFESP", "unifesp.br")
        prof = make_professor(db, "Prof Ja Membro", "jamembro@unifesp.br")
        group = group_service.create_group(db, prof, "Grupo UNIFESP", inst.id)
        link_professor_institution(db, prof, inst, email="prof2@unifesp.br")

        with pytest.raises(ValueError, match="ja_membro"):
            group_service.join_group(db, prof, group.id, inst.id)

    def test_raises_when_group_not_found(self, db):
        inst = make_institution(db, "UNESP", "unesp.br")
        prof = make_professor(db, "Prof UNESP", "prof@unesp.br")
        link_professor_institution(db, prof, inst)

        with pytest.raises(ValueError, match="grupo_nao_encontrado"):
            group_service.join_group(db, prof, 9999, inst.id)


class TestLeaveGroup:
    def test_professor_leaves_group(self, db):
        inst = make_institution(db, "IME", "ime.br")
        prof1 = make_professor(db, "Prof Coord IME", "coord@ime.br")
        prof2 = make_professor(db, "Prof Member IME", "member@ime.br")
        group = group_service.create_group(db, prof1, "Grupo IME", inst.id)
        link_professor_institution(db, prof2, inst)
        group_service.join_group(db, prof2, group.id, inst.id)

        group_service.leave_group(db, prof2, group.id)
        pg = db.query(ProfessorGroup).filter_by(professor_id=prof2.id, group_id=group.id).first()
        assert pg is None

    def test_raises_when_not_member(self, db):
        inst = make_institution(db, "ITA", "ita.br")
        prof = make_professor(db, "Prof ITA", "prof@ita.br")
        group = group_service.create_group_direct(db, "Grupo ITA", inst.id)

        with pytest.raises(ValueError, match="nao_membro"):
            group_service.leave_group(db, prof, group.id)

    def test_raises_when_only_coordinator(self, db):
        inst = make_institution(db, "ESALQ", "esalq.br")
        prof = make_professor(db, "Prof Unico Coord", "unico@esalq.br")
        group = group_service.create_group(db, prof, "Grupo ESALQ", inst.id)

        with pytest.raises(ValueError, match="unico_coordinator"):
            group_service.leave_group(db, prof, group.id)


class TestUpdateGroup:
    def test_updates_name(self, db):
        inst = make_institution(db, "FEA", "fea.br")
        prof = make_professor(db, "Prof FEA", "prof@fea.br")
        group = group_service.create_group(db, prof, "Grupo Antigo", inst.id)

        updated = group_service.update_group(db, group, {"name": "Grupo Novo"})
        assert updated.name == "Grupo Novo"


class TestGetGroupById:
    def test_returns_group(self, db):
        inst = make_institution(db, "FMUSP", "fmusp.br")
        group = group_service.create_group_direct(db, "Grupo FMUSP", inst.id)
        result = group_service.get_group_by_id(db, group.id)
        assert result is not None
        assert result.id == group.id

    def test_returns_none_for_unknown_id(self, db):
        result = group_service.get_group_by_id(db, 9999)
        assert result is None

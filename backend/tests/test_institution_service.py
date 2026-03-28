"""Tests for app/services/institution_service.py"""
import pytest
from passlib.context import CryptContext

from app.models import Institution, Professor, ProfessorInstitution, User
from app.services import institution_service

pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")


def make_professor(db, nome="Prof Inst", email=None):
    if email is None:
        email = f"prof_{nome.lower().replace(' ', '_')}@test.br"
    prof = Professor(nome=nome, ativo=True)
    db.add(prof)
    db.flush()
    user = User(
        email=email,
        nome=nome,
        password_hash=pwd_ctx.hash("testpass"),
        role="professor",
        is_admin=False,
        professor_id=prof.id,
    )
    db.add(user)
    db.commit()
    db.refresh(prof)
    return prof


class TestGetOrCreateInstitution:
    def test_creates_new_institution(self, db):
        inst = institution_service.get_or_create_institution(db, "unicamp.br")
        assert inst.id is not None
        assert inst.domain == "unicamp.br"
        assert inst.name == "UNICAMP"

    def test_returns_existing_institution(self, db):
        inst1 = institution_service.get_or_create_institution(db, "usp.br")
        db.commit()
        inst2 = institution_service.get_or_create_institution(db, "usp.br")
        assert inst1.id == inst2.id

    def test_name_derived_from_domain(self, db):
        inst = institution_service.get_or_create_institution(db, "ufrgs.br")
        assert inst.name == "UFRGS"


class TestListAll:
    def test_returns_all_institutions(self, db):
        institution_service.get_or_create_institution(db, "abc.br")
        institution_service.get_or_create_institution(db, "xyz.br")
        db.commit()
        result = institution_service.list_all(db)
        assert len(result) >= 2


class TestGetById:
    def test_returns_institution(self, db):
        inst = institution_service.get_or_create_institution(db, "ufmg.br")
        db.commit()
        found = institution_service.get_by_id(db, inst.id)
        assert found is not None
        assert found.id == inst.id

    def test_returns_none_for_unknown_id(self, db):
        result = institution_service.get_by_id(db, 9999)
        assert result is None


class TestListProfessorEmails:
    def test_returns_emails(self, db):
        prof = make_professor(db, "Prof Email List", "listemail@test.br")
        institution_service.add_institutional_email(db, prof, "listemail@ufsc.br")
        result = institution_service.list_professor_emails(db, prof)
        assert len(result) == 1
        assert result[0].institutional_email == "listemail@ufsc.br"

    def test_empty_when_no_emails(self, db):
        prof = make_professor(db, "Prof No Emails", "noemails@test.br")
        result = institution_service.list_professor_emails(db, prof)
        assert result == []


class TestAddInstitutionalEmail:
    def test_adds_email(self, db):
        prof = make_professor(db, "Prof Add Email", "addemail@test.br")
        pi = institution_service.add_institutional_email(db, prof, "profadd@ufsc.br")
        assert pi.id is not None
        assert pi.institutional_email == "profadd@ufsc.br"
        assert pi.professor_id == prof.id

    def test_creates_institution_if_not_exists(self, db):
        prof = make_professor(db, "Prof New Domain", "newdomain@test.br")
        institution_service.add_institutional_email(db, prof, "prof@newinst.br")
        inst = db.query(Institution).filter_by(domain="newinst.br").first()
        assert inst is not None

    def test_raises_on_public_email(self, db):
        prof = make_professor(db, "Prof Gmail", "gmail@test.br")
        with pytest.raises(ValueError, match="email_publico"):
            institution_service.add_institutional_email(db, prof, "prof@gmail.com")

    def test_raises_on_duplicate_email(self, db):
        prof1 = make_professor(db, "Prof Dup1", "dup1@test.br")
        prof2 = make_professor(db, "Prof Dup2", "dup2@test.br")
        institution_service.add_institutional_email(db, prof1, "dup@ufba.br")
        with pytest.raises(ValueError, match="email_duplicado"):
            institution_service.add_institutional_email(db, prof2, "dup@ufba.br")

    def test_raises_on_duplicate_institution(self, db):
        prof = make_professor(db, "Prof Dup Inst", "dupinst@test.br")
        institution_service.add_institutional_email(db, prof, "x@ufpb.br")
        with pytest.raises(ValueError, match="instituicao_duplicada"):
            institution_service.add_institutional_email(db, prof, "y@ufpb.br")

    def test_creates_group_for_new_institution(self, db):
        from app.models import ResearchGroup
        prof = make_professor(db, "Prof Group Create", "groupcreate@test.br")
        institution_service.add_institutional_email(db, prof, "prof@groupcreate.br")
        inst = db.query(Institution).filter_by(domain="groupcreate.br").first()
        group = db.query(ResearchGroup).filter_by(institution_id=inst.id).first()
        assert group is not None


class TestRemoveInstitutionalEmail:
    def test_removes_email(self, db):
        prof = make_professor(db, "Prof Remove Email", "removeemail@test.br")
        institution_service.add_institutional_email(db, prof, "rm1@inst1.br")
        pi2 = institution_service.add_institutional_email(db, prof, "rm2@inst2.br")
        institution_service.remove_institutional_email(db, prof, pi2.id)
        found = db.query(ProfessorInstitution).filter_by(id=pi2.id).first()
        assert found is None

    def test_raises_when_only_one_email(self, db):
        prof = make_professor(db, "Prof Unico Email", "unicoemail@test.br")
        pi = institution_service.add_institutional_email(db, prof, "single@inst.br")
        with pytest.raises(ValueError, match="minimo_um_email"):
            institution_service.remove_institutional_email(db, prof, pi.id)

    def test_raises_when_not_found(self, db):
        prof = make_professor(db, "Prof Email NF", "emailnf@test.br")
        institution_service.add_institutional_email(db, prof, "nf1@nf.br")
        institution_service.add_institutional_email(db, prof, "nf2@nf2.br")
        with pytest.raises(ValueError, match="nao_encontrado"):
            institution_service.remove_institutional_email(db, prof, 9999)

"""Tests for app/routers/deadlines.py"""
from datetime import date

from app.models import Deadline, Institution
from app.routers.auth import make_token

from .conftest import make_user


def make_deadline(db, user_id, label="Deadline Test", url="http://example.com", date_val=None):
    d = Deadline(
        label=label,
        url=url,
        date=date_val or date.today(),
        created_by_id=user_id,
    )
    db.add(d)
    db.commit()
    db.refresh(d)
    return d


class TestListDeadlines:
    def test_list_deadlines_empty(self, client, db):
        user = make_user(db, email="listdl@univ.br", role="researcher")
        token = make_token(user)
        resp = client.get("/api/deadlines/", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_list_deadlines_with_data(self, client, db):
        user = make_user(db, email="listdl2@univ.br", role="researcher")
        token = make_token(user)
        make_deadline(db, user.id, label="Test DL")
        resp = client.get("/api/deadlines/", headers={"Authorization": f"Bearer {token}"})
        assert len(resp.json()) >= 1

    def test_requires_auth(self, client, db):
        resp = client.get("/api/deadlines/")
        assert resp.status_code in (401, 403)


class TestCreateDeadline:
    def test_creates_deadline(self, client, db):
        user = make_user(db, email="createdl@univ.br", role="professor")
        token = make_token(user)
        resp = client.post(
            "/api/deadlines/",
            json={"label": "ICSE 2026", "url": "http://icse.org", "date": str(date.today())},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 201
        assert resp.json()["label"] == "ICSE 2026"

    def test_creates_deadline_as_researcher(self, client, db):
        user = make_user(db, email="rdl@univ.br", role="researcher")
        token = make_token(user)
        resp = client.post(
            "/api/deadlines/",
            json={"label": "Workshop X", "url": "http://workshop.org", "date": str(date.today())},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 201


class TestDeleteDeadline:
    def test_creator_can_delete(self, client, db):
        user = make_user(db, email="deldl@univ.br", role="professor")
        token = make_token(user)
        create_resp = client.post(
            "/api/deadlines/",
            json={"label": "Del DL", "url": "http://del.com", "date": str(date.today())},
            headers={"Authorization": f"Bearer {token}"},
        )
        dl_id = create_resp.json()["id"]
        del_resp = client.delete(f"/api/deadlines/{dl_id}", headers={"Authorization": f"Bearer {token}"})
        assert del_resp.status_code == 204

    def test_returns_404_for_unknown(self, client, db):
        user = make_user(db, email="deldl404@univ.br", role="professor")
        token = make_token(user)
        resp = client.delete("/api/deadlines/9999", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 404

    def test_non_creator_researcher_cannot_delete(self, client, db):
        creator = make_user(db, email="dlcreator@univ.br", role="professor")
        other = make_user(db, email="dlother@univ.br", role="researcher")
        deadline = make_deadline(db, creator.id, label="Creator DL")
        token = make_token(other)
        resp = client.delete(f"/api/deadlines/{deadline.id}", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 403

    def test_professor_can_delete_any(self, client, db):
        researcher = make_user(db, email="dlresearcher@univ.br", role="researcher")
        prof = make_user(db, email="dlprof@univ.br", role="professor")
        deadline = make_deadline(db, researcher.id, label="R DL")
        token = make_token(prof)
        resp = client.delete(f"/api/deadlines/{deadline.id}", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 204


class TestToggleInterest:
    def test_toggle_adds_interest(self, client, db):
        user = make_user(db, email="interest@univ.br", role="researcher")
        token = make_token(user)
        deadline = make_deadline(db, user.id, label="Interest DL")
        resp = client.post(f"/api/deadlines/{deadline.id}/interest", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 204

    def test_toggle_removes_interest(self, client, db):
        user = make_user(db, email="uninterest@univ.br", role="researcher")
        token = make_token(user)
        deadline = make_deadline(db, user.id, label="Uninterest DL")
        client.post(f"/api/deadlines/{deadline.id}/interest", headers={"Authorization": f"Bearer {token}"})
        resp = client.post(f"/api/deadlines/{deadline.id}/interest", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 204

    def test_toggle_interest_404(self, client, db):
        user = make_user(db, email="interest404@univ.br", role="researcher")
        token = make_token(user)
        resp = client.post("/api/deadlines/9999/interest", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 404


class TestInstitutionFiltering:
    """Garante que /deadlines?institution_id= filtra corretamente.

    Cenário: existem deadlines na base para a instituição A.
    Ao carregar o /app/group de um grupo da instituição B (sem deadlines),
    a API deve retornar lista vazia — não vazar os deadlines de A.
    """

    def _make_institution(self, db, name, domain):
        inst = Institution(name=name, domain=domain)
        db.add(inst)
        db.commit()
        db.refresh(inst)
        return inst

    def test_group_without_deadlines_returns_empty(self, client, db):
        user = make_user(db, email="filterdl@univ.br", role="researcher")
        token = make_token(user)

        inst_a = self._make_institution(db, "Inst A", "insta.br")
        inst_b = self._make_institution(db, "Inst B", "instb.br")  # sem deadlines

        # Cria vários deadlines vinculados à instituição A
        for i in range(3):
            db.add(Deadline(
                label=f"DL Inst A {i}",
                url="http://example.com",
                date=date.today(),
                institution_id=inst_a.id,
                created_by_id=user.id,
            ))
        db.commit()

        # Busca com institution_id de B — deve retornar vazio
        resp = client.get(
            f"/api/deadlines/?institution_id={inst_b.id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        assert resp.json() == [], (
            "Deadlines de outras instituições não devem aparecer ao filtrar por inst_b"
        )

    def test_without_filter_returns_all(self, client, db):
        """Sem institution_id a API retorna tudo — comportamento que o guard no
        frontend deve evitar chamar enquanto currentInstitution === undefined."""
        user = make_user(db, email="nofilterdl@univ.br", role="researcher")
        token = make_token(user)

        inst = self._make_institution(db, "Inst NF", "instnf.br")
        for i in range(2):
            db.add(Deadline(
                label=f"DL NF {i}",
                url="http://example.com",
                date=date.today(),
                institution_id=inst.id,
                created_by_id=user.id,
            ))
        db.commit()

        resp = client.get("/api/deadlines/", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        assert len(resp.json()) >= 2

    def test_filter_returns_only_own_institution(self, client, db):
        user = make_user(db, email="owninstdl@univ.br", role="researcher")
        token = make_token(user)

        inst_a = self._make_institution(db, "Own A", "owna.br")
        inst_b = self._make_institution(db, "Own B", "ownb.br")

        db.add(Deadline(label="DL A", url="http://a.com", date=date.today(),
                        institution_id=inst_a.id, created_by_id=user.id))
        db.add(Deadline(label="DL B", url="http://b.com", date=date.today(),
                        institution_id=inst_b.id, created_by_id=user.id))
        db.commit()

        resp = client.get(
            f"/api/deadlines/?institution_id={inst_a.id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["label"] == "DL A"
        assert all(d["institution_id"] == inst_a.id for d in data)


class TestListInterests:
    def test_list_interests(self, client, db):
        user = make_user(db, email="listinterests@univ.br", role="researcher")
        token = make_token(user)
        resp = client.get("/api/deadlines/interests", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

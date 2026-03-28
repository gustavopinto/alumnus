"""Tests for app/routers/deadlines.py"""
from datetime import date

from app.models import Deadline
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


class TestListInterests:
    def test_list_interests(self, client, db):
        user = make_user(db, email="listinterests@univ.br", role="researcher")
        token = make_token(user)
        resp = client.get("/api/deadlines/interests", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

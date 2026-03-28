"""Tests for app/routers/notes.py"""
from app.routers.auth import make_token
from app.services import note_service

from .conftest import make_user


class TestListNotes:
    def test_professor_can_list_notes(self, client, db):
        prof = make_user(db, email="profnotes@univ.br", role="professor")
        target = make_user(db, email="researchernotes@univ.br", role="researcher")
        token = make_token(prof)
        resp = client.get(
            f"/api/users/{target.id}/notes",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_researcher_can_list_own_notes(self, client, db):
        user = make_user(db, email="self_notes@univ.br", role="researcher")
        token = make_token(user)
        resp = client.get(
            f"/api/users/{user.id}/notes",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200

    def test_researcher_cannot_list_others_notes(self, client, db):
        user1 = make_user(db, email="rother1notes@univ.br", role="researcher")
        user2 = make_user(db, email="rother2notes@univ.br", role="researcher")
        token = make_token(user1)
        resp = client.get(
            f"/api/users/{user2.id}/notes",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 403

    def test_requires_auth(self, client, db):
        user = make_user(db, email="noauth_notes@univ.br", role="researcher")
        resp = client.get(f"/api/users/{user.id}/notes")
        assert resp.status_code in (401, 403)


class TestCreateNote:
    def test_professor_creates_note(self, client, db):
        prof = make_user(db, email="profrcrn@univ.br", role="professor")
        target = make_user(db, email="targetcn@univ.br", role="researcher")
        token = make_token(prof)
        resp = client.post(
            f"/api/users/{target.id}/notes",
            data={"text": "Nota de teste"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 201
        assert resp.json()["text"] == "Nota de teste"

    def test_researcher_creates_own_note(self, client, db):
        user = make_user(db, email="selfnote@univ.br", role="researcher")
        token = make_token(user)
        resp = client.post(
            f"/api/users/{user.id}/notes",
            data={"text": "Minha nota"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 201
        assert resp.json()["text"] == "Minha nota"

    def test_researcher_cannot_create_note_for_other(self, client, db):
        user1 = make_user(db, email="rnotecreate1@univ.br", role="researcher")
        user2 = make_user(db, email="rnotecreate2@univ.br", role="researcher")
        token = make_token(user1)
        resp = client.post(
            f"/api/users/{user2.id}/notes",
            data={"text": "Sem permissao"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 403


class TestDeleteNote:
    def test_professor_deletes_note(self, client, db):
        prof = make_user(db, email="profdnote@univ.br", role="professor")
        target = make_user(db, email="targetdn@univ.br", role="researcher")
        token = make_token(prof)
        create_resp = client.post(
            f"/api/users/{target.id}/notes",
            data={"text": "Para deletar"},
            headers={"Authorization": f"Bearer {token}"},
        )
        note_id = create_resp.json()["id"]
        del_resp = client.delete(
            f"/api/notes/{note_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert del_resp.status_code == 204

    def test_returns_404_for_unknown(self, client, db):
        prof = make_user(db, email="profdn404@univ.br", role="professor")
        token = make_token(prof)
        resp = client.delete(
            "/api/notes/9999",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 404

    def test_researcher_cannot_delete_others_note(self, client, db):
        prof = make_user(db, email="profdn_other@univ.br", role="professor")
        user = make_user(db, email="targetdn_other@univ.br", role="researcher")
        other = make_user(db, email="otherdn@univ.br", role="researcher")
        prof_token = make_token(prof)
        create_resp = client.post(
            f"/api/users/{user.id}/notes",
            data={"text": "Nao pode deletar"},
            headers={"Authorization": f"Bearer {prof_token}"},
        )
        note_id = create_resp.json()["id"]
        other_token = make_token(other)
        resp = client.delete(
            f"/api/notes/{note_id}",
            headers={"Authorization": f"Bearer {other_token}"},
        )
        assert resp.status_code == 403

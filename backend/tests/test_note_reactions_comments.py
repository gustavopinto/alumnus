"""Testes de integração para reactions e comments em notas."""
import pytest
from app.routers.auth import make_token
from app.models import Note
from .conftest import make_user


class TestNoteReactions:
    def test_toggle_reaction_adds(self, client, db):
        prof = make_user(db, email="prof_react@test.br", role="professor")
        target = make_user(db, email="target_react@test.br", role="researcher")
        token = make_token(prof)
        note_resp = client.post(
            f"/api/users/{target.id}/notes",
            data={"text": "Nota para reação"},
            headers={"Authorization": f"Bearer {token}"},
        )
        note_id = note_resp.json()["id"]

        resp = client.post(
            f"/api/notes/{note_id}/reactions",
            json={"reaction_type": "like"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 204

    def test_toggle_reaction_removes_when_same(self, client, db):
        prof = make_user(db, email="prof_react2@test.br", role="professor")
        target = make_user(db, email="target_react2@test.br", role="researcher")
        token = make_token(prof)
        note_resp = client.post(
            f"/api/users/{target.id}/notes",
            data={"text": "Nota para toggle"},
            headers={"Authorization": f"Bearer {token}"},
        )
        note_id = note_resp.json()["id"]
        # Adiciona
        client.post(f"/api/notes/{note_id}/reactions", json={"reaction_type": "like"}, headers={"Authorization": f"Bearer {token}"})
        # Toggle off
        resp = client.post(f"/api/notes/{note_id}/reactions", json={"reaction_type": "like"}, headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 204

    def test_reaction_invalid_type_returns_422(self, client, db):
        prof = make_user(db, email="prof_react3@test.br", role="professor")
        target = make_user(db, email="target_react3@test.br", role="researcher")
        token = make_token(prof)
        note_resp = client.post(f"/api/users/{target.id}/notes", data={"text": "X"}, headers={"Authorization": f"Bearer {token}"})
        note_id = note_resp.json()["id"]
        resp = client.post(f"/api/notes/{note_id}/reactions", json={"reaction_type": "angry"}, headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 422

    def test_reaction_requires_auth(self, client, db):
        prof = make_user(db, email="prof_react4@test.br", role="professor")
        target = make_user(db, email="target_react4@test.br", role="researcher")
        token = make_token(prof)
        note_resp = client.post(f"/api/users/{target.id}/notes", data={"text": "X"}, headers={"Authorization": f"Bearer {token}"})
        note_id = note_resp.json()["id"]
        resp = client.post(f"/api/notes/{note_id}/reactions", json={"reaction_type": "like"})
        assert resp.status_code in (401, 403)

    def test_reactions_appear_in_note_list(self, client, db):
        prof = make_user(db, email="prof_react5@test.br", role="professor")
        target = make_user(db, email="target_react5@test.br", role="researcher")
        token = make_token(prof)
        note_resp = client.post(f"/api/users/{target.id}/notes", data={"text": "Nota com reação"}, headers={"Authorization": f"Bearer {token}"})
        note_id = note_resp.json()["id"]
        client.post(f"/api/notes/{note_id}/reactions", json={"reaction_type": "happy"}, headers={"Authorization": f"Bearer {token}"})
        notes = client.get(f"/api/users/{target.id}/notes", headers={"Authorization": f"Bearer {token}"}).json()
        note = next(n for n in notes if n["id"] == note_id)
        assert any(r["type"] == "happy" for r in note["reactions"])


class TestNoteComments:
    def test_add_comment(self, client, db):
        prof = make_user(db, email="prof_cmt@test.br", role="professor")
        target = make_user(db, email="target_cmt@test.br", role="researcher")
        token = make_token(prof)
        note_resp = client.post(f"/api/users/{target.id}/notes", data={"text": "Nota"}, headers={"Authorization": f"Bearer {token}"})
        note_id = note_resp.json()["id"]
        resp = client.post(f"/api/notes/{note_id}/comments", json={"text": "Ótima nota!"}, headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 201
        assert resp.json()["text"] == "Ótima nota!"

    def test_delete_comment(self, client, db):
        prof = make_user(db, email="prof_cmt2@test.br", role="professor")
        target = make_user(db, email="target_cmt2@test.br", role="researcher")
        token = make_token(prof)
        note_resp = client.post(f"/api/users/{target.id}/notes", data={"text": "Nota"}, headers={"Authorization": f"Bearer {token}"})
        note_id = note_resp.json()["id"]
        cmt_resp = client.post(f"/api/notes/{note_id}/comments", json={"text": "Comentário"}, headers={"Authorization": f"Bearer {token}"})
        cmt_id = cmt_resp.json()["id"]
        del_resp = client.delete(f"/api/notes/comments/{cmt_id}", headers={"Authorization": f"Bearer {token}"})
        assert del_resp.status_code == 204

    def test_comments_appear_in_note_list(self, client, db):
        prof = make_user(db, email="prof_cmt3@test.br", role="professor")
        target = make_user(db, email="target_cmt3@test.br", role="researcher")
        token = make_token(prof)
        note_resp = client.post(f"/api/users/{target.id}/notes", data={"text": "Nota"}, headers={"Authorization": f"Bearer {token}"})
        note_id = note_resp.json()["id"]
        client.post(f"/api/notes/{note_id}/comments", json={"text": "Bom trabalho!"}, headers={"Authorization": f"Bearer {token}"})
        notes = client.get(f"/api/users/{target.id}/notes", headers={"Authorization": f"Bearer {token}"}).json()
        note = next(n for n in notes if n["id"] == note_id)
        assert any(c["text"] == "Bom trabalho!" for c in note["comments"])

    def test_researcher_cannot_delete_others_comment(self, client, db):
        prof = make_user(db, email="prof_cmt4@test.br", role="professor")
        r1 = make_user(db, email="r1_cmt@test.br", role="researcher")
        r2 = make_user(db, email="r2_cmt@test.br", role="researcher")
        token_prof = make_token(prof)
        token_r2 = make_token(r2)
        note_resp = client.post(f"/api/users/{r1.id}/notes", data={"text": "Nota"}, headers={"Authorization": f"Bearer {token_prof}"})
        note_id = note_resp.json()["id"]
        cmt_resp = client.post(f"/api/notes/{note_id}/comments", json={"text": "Comentário do prof"}, headers={"Authorization": f"Bearer {token_prof}"})
        cmt_id = cmt_resp.json()["id"]
        del_resp = client.delete(f"/api/notes/comments/{cmt_id}", headers={"Authorization": f"Bearer {token_r2}"})
        assert del_resp.status_code == 403

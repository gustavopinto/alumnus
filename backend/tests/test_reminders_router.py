"""Tests for app/routers/reminders.py"""
from app.routers.auth import make_token

from .conftest import make_reminder, make_user


class TestListReminders:
    def test_list_without_auth(self, client, db):
        resp = client.get("/api/reminders/")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_list_with_auth(self, client, db):
        user = make_user(db, email="listrem@univ.br")
        token = make_token(user)
        resp = client.get("/api/reminders/", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200

    def test_list_shows_created_reminder(self, client, db):
        user = make_user(db, email="listrem2@univ.br")
        make_reminder(db, text="Lembrete teste", created_by_id=user.id)
        resp = client.get("/api/reminders/")
        assert len(resp.json()) >= 1


class TestCreateReminder:
    def test_creates_reminder_with_auth(self, client, db):
        user = make_user(db, email="createrem@univ.br")
        token = make_token(user)
        resp = client.post(
            "/api/reminders/",
            json={"text": "Lembrar de X"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 201
        assert resp.json()["text"] == "Lembrar de X"

    def test_creates_reminder_without_auth(self, client, db):
        resp = client.post("/api/reminders/", json={"text": "Sem auth"})
        assert resp.status_code == 201
        assert resp.json()["text"] == "Sem auth"

    def test_creates_reminder_with_due_date(self, client, db):
        resp = client.post("/api/reminders/", json={"text": "Com data", "due_date": "2026-12-31"})
        assert resp.status_code == 201
        assert resp.json()["due_date"] == "2026-12-31"


class TestUpdateReminder:
    def test_updates_text(self, client, db):
        user = make_user(db, email="updaterem@univ.br")
        token = make_token(user)
        create_resp = client.post(
            "/api/reminders/",
            json={"text": "Original"},
            headers={"Authorization": f"Bearer {token}"},
        )
        rem_id = create_resp.json()["id"]
        update_resp = client.put(
            f"/api/reminders/{rem_id}",
            json={"text": "Atualizado", "done": False},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert update_resp.status_code == 200
        assert update_resp.json()["text"] == "Atualizado"

    def test_marks_done(self, client, db):
        create_resp = client.post("/api/reminders/", json={"text": "Para marcar"})
        rem_id = create_resp.json()["id"]
        update_resp = client.put(f"/api/reminders/{rem_id}", json={"text": "Para marcar", "done": True})
        assert update_resp.status_code == 200
        assert update_resp.json()["done"] is True

    def test_returns_404_for_unknown(self, client, db):
        resp = client.put("/api/reminders/9999", json={"text": "X", "done": False})
        assert resp.status_code == 404


class TestDeleteReminder:
    def test_deletes_own_reminder(self, client, db):
        user = make_user(db, email="deletrem@univ.br")
        token = make_token(user)
        reminder = make_reminder(db, text="Para deletar", created_by_id=user.id)
        resp = client.delete(f"/api/reminders/{reminder.id}", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 204

    def test_returns_404_for_unknown(self, client, db):
        user = make_user(db, email="delrem404@univ.br")
        token = make_token(user)
        resp = client.delete("/api/reminders/9999", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 404

    def test_cannot_delete_others_reminder(self, client, db):
        owner = make_user(db, email="remowner@univ.br", role="researcher")
        other = make_user(db, email="remotherdel@univ.br", role="researcher")
        reminder = make_reminder(db, text="Alheio", created_by_id=owner.id)
        token = make_token(other)
        resp = client.delete(f"/api/reminders/{reminder.id}", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 403

    def test_requires_auth_to_delete(self, client, db):
        reminder = make_reminder(db, text="Auth required")
        resp = client.delete(f"/api/reminders/{reminder.id}")
        assert resp.status_code in (401, 403)


class TestReminderWithHtml:
    def test_creates_reminder_with_html(self, client, db):
        user = make_user(db, email="htmlreminder@univ.br", role="professor")
        token = make_token(user)
        html = '<p>Lembrete com <span data-type="mention" data-id="ana-silva" class="mention">@Ana Silva</span></p>'
        resp = client.post(
            "/api/reminders/",
            json={"text": html, "due_date": None},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 201
        assert 'data-type="mention"' in resp.json()["text"]

    def test_creates_reminder_with_bold_html(self, client, db):
        user = make_user(db, email="boldreminder@univ.br", role="professor")
        token = make_token(user)
        html = '<p><strong>Importante:</strong> reunião amanhã</p>'
        resp = client.post(
            "/api/reminders/",
            json={"text": html, "due_date": None},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 201
        assert '<strong>' in resp.json()["text"]

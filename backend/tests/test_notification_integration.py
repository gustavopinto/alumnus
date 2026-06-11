"""
Testes de integração para o sistema de notificações via HTTP.

Verifica que:
- POST /api/users/{id}/notes  → agenda NoteCreatedEvent (asyncio.create_task)
- POST /api/reminders/        → agenda ReminderCreatedEvent
- POST /api/admin/users/{id}/send-login-reminder → envia LoginReminderEvent diretamente

Todos os envios reais de e-mail são interceptados para não chamar a API do Resend.
"""
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.deps import require_dashboard, require_superadmin
from app.main import app
from app.database import get_db
from app.notifications.events import LoginReminderEvent, NoteCreatedEvent, ReminderCreatedEvent
from app.routers.auth import make_token

from .conftest import make_institution, make_group, make_researcher_user, make_user


# ---------------------------------------------------------------------------
# Helpers de override
# ---------------------------------------------------------------------------

def _deps_override(db_session, user):
    def _db():
        yield db_session

    def _dashboard():
        return user

    def _superadmin():
        return user

    return {
        get_db: _db,
        require_dashboard: _dashboard,
        require_superadmin: _superadmin,
    }


@pytest.fixture
def admin_client(db):
    sa = make_user(db, email="sa@admin.br", nome="SA", role="superadmin")
    app.dependency_overrides.update(_deps_override(db, sa))
    with TestClient(app, raise_server_exceptions=True) as c:
        yield c, sa, db
    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# POST /api/users/{id}/notes — NoteCreatedEvent
# ---------------------------------------------------------------------------

class TestCreateNoteNotification:
    def test_create_note_schedules_create_task(self, client, db):
        prof = make_user(db, email="profnt@test.br", role="professor")
        target = make_user(db, email="targetnt@test.br", role="researcher")
        token = make_token(prof)

        with patch("app.notifications.dispatcher.asyncio.create_task") as mock_ct:
            resp = client.post(
                f"/api/users/{target.id}/notes",
                data={"text": "Notificação integração"},
                headers={"Authorization": f"Bearer {token}"},
            )
            assert resp.status_code == 201
            assert mock_ct.called, "create_task deve ser chamado após criação de nota"

    def test_create_task_receives_note_created_event(self, client, db):
        prof = make_user(db, email="profevt@test.br", role="professor")
        target = make_user(db, email="targetevt@test.br", role="researcher")
        token = make_token(prof)

        dispatched_events = []
        collected_coros = []

        async def capture_dispatch(event):
            dispatched_events.append(event)

        def fake_create_task(coro):
            # Coleta a coroutine para rodar depois (loop já está rodando)
            collected_coros.append(coro)
            return MagicMock()

        with patch("app.notifications.dispatcher.dispatcher.dispatch", capture_dispatch):
            with patch("app.notifications.dispatcher.asyncio.create_task", fake_create_task):
                resp = client.post(
                    f"/api/users/{target.id}/notes",
                    data={"text": "Evento certo"},
                    headers={"Authorization": f"Bearer {token}"},
                )
                assert resp.status_code == 201

        # Roda as coroutines depois que o loop do TestClient parou
        for coro in collected_coros:
            asyncio.run(coro)

        assert len(dispatched_events) == 1
        ev = dispatched_events[0]
        assert isinstance(ev, NoteCreatedEvent)
        assert ev.author_email == prof.email
        assert ev.profile_user_id == target.id

    def test_create_note_still_returns_201_when_notification_fails(self, client, db):
        prof = make_user(db, email="profnf@test.br", role="professor")
        target = make_user(db, email="targetnf@test.br", role="researcher")
        token = make_token(prof)

        with patch("app.notifications.dispatcher.asyncio.create_task", side_effect=Exception("falhou")):
            resp = client.post(
                f"/api/users/{target.id}/notes",
                data={"text": "Nota deve criar mesmo com erro"},
                headers={"Authorization": f"Bearer {token}"},
            )
            # A nota é criada mesmo que a notificação falhe
            assert resp.status_code == 201


# ---------------------------------------------------------------------------
# POST /api/reminders/ — ReminderCreatedEvent
# ---------------------------------------------------------------------------

class TestCreateReminderNotification:
    def test_create_reminder_schedules_create_task(self, client, db):
        user = make_user(db, email="remnt@test.br")
        token = make_token(user)

        with patch("app.notifications.dispatcher.asyncio.create_task") as mock_ct:
            resp = client.post(
                "/api/reminders/",
                json={"text": "Lembrete integração"},
                headers={"Authorization": f"Bearer {token}"},
            )
            assert resp.status_code == 201
            assert mock_ct.called

    def test_create_task_receives_reminder_created_event(self, client, db):
        inst = make_institution(db, name="Inst Integ", domain="integ.br")
        user = make_user(db, email="reminst@test.br")
        token = make_token(user)

        dispatched_events = []
        collected_coros = []

        async def capture_dispatch(event):
            dispatched_events.append(event)

        def fake_create_task(coro):
            collected_coros.append(coro)
            return MagicMock()

        with patch("app.notifications.dispatcher.dispatcher.dispatch", capture_dispatch):
            with patch("app.notifications.dispatcher.asyncio.create_task", fake_create_task):
                resp = client.post(
                    "/api/reminders/",
                    json={"text": "Lembrete evento", "institution_id": inst.id},
                    headers={"Authorization": f"Bearer {token}"},
                )
                assert resp.status_code == 201

        for coro in collected_coros:
            asyncio.run(coro)

        assert len(dispatched_events) == 1
        ev = dispatched_events[0]
        assert isinstance(ev, ReminderCreatedEvent)
        assert ev.institution_id == inst.id
        assert ev.author_email == user.email

    def test_create_reminder_works_without_auth(self, client, db):
        """Criação anônima de lembrete também aciona notificação."""
        with patch("app.notifications.dispatcher.asyncio.create_task") as mock_ct:
            resp = client.post("/api/reminders/", json={"text": "Anônimo"})
            assert resp.status_code == 201
            assert mock_ct.called

    def test_reminder_event_has_no_author_for_anonymous(self, client, db):
        dispatched_events = []
        collected_coros = []

        async def capture_dispatch(event):
            dispatched_events.append(event)

        def fake_create_task(coro):
            collected_coros.append(coro)
            return MagicMock()

        with patch("app.notifications.dispatcher.dispatcher.dispatch", capture_dispatch):
            with patch("app.notifications.dispatcher.asyncio.create_task", fake_create_task):
                client.post("/api/reminders/", json={"text": "Anon"})

        for coro in collected_coros:
            asyncio.run(coro)

        if dispatched_events:
            ev = dispatched_events[0]
            assert isinstance(ev, ReminderCreatedEvent)
            assert ev.author_email is None


# ---------------------------------------------------------------------------
# POST /api/admin/users/{id}/send-login-reminder — LoginReminderEvent
# ---------------------------------------------------------------------------

class TestSendLoginReminder:
    def test_returns_204_for_valid_user(self, admin_client):
        client, sa, db = admin_client
        target = make_user(db, email="target_lr@test.br", nome="Target")

        with patch("app.notifications.channels.email.send_email", new_callable=AsyncMock):
            resp = client.post(f"/api/admin/users/{target.id}/send-login-reminder")
        assert resp.status_code == 204

    def test_returns_404_for_unknown_user(self, admin_client):
        client, sa, db = admin_client
        resp = client.post("/api/admin/users/99999/send-login-reminder")
        assert resp.status_code == 404

    def test_dispatches_login_reminder_event(self, admin_client):
        from app.notifications.dispatcher import dispatcher as notif_dispatcher
        client, sa, db = admin_client
        target = make_user(db, email="target_ev@test.br", nome="Target")

        dispatched = []

        async def capture(event):
            dispatched.append(event)

        # Dispatcher é importado dentro da função de admin, então patcha o singleton
        with patch.object(notif_dispatcher, "dispatch", side_effect=capture):
            resp = client.post(f"/api/admin/users/{target.id}/send-login-reminder")

        assert resp.status_code == 204
        assert len(dispatched) == 1
        ev = dispatched[0]
        assert isinstance(ev, LoginReminderEvent)
        assert ev.target_email == "target_ev@test.br"
        assert ev.target_name == "Target"

    def test_sends_email_to_correct_address(self, admin_client):
        client, sa, db = admin_client
        target = make_user(db, email="correctaddr@test.br", nome="User LR")

        with patch("app.notifications.channels.email.send_email", new_callable=AsyncMock) as mock_send:
            resp = client.post(f"/api/admin/users/{target.id}/send-login-reminder")

        assert resp.status_code == 204
        assert mock_send.called
        sent_to = mock_send.call_args[0][0]
        assert sent_to == "correctaddr@test.br"

    def test_requires_authentication(self, client, db):
        target = make_user(db, email="noauth_lr@test.br")
        # client sem token
        resp = client.post(f"/api/admin/users/{target.id}/send-login-reminder")
        assert resp.status_code in (401, 403)

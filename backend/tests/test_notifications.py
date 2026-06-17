"""
Testes de unidade para o sistema de notificações.

Cobre:
- app/notifications/events.py
- app/notifications/dispatcher.py  (NotificationDispatcher + @notifies)
- app/notifications/channels/base.py
- app/notifications/channels/email.py  (EmailChannel + _institution_member_emails)
- app/services/email_service.py
- app/services/email_templates.py  (reminder_created_html, login_reminder_html)
"""
import asyncio
from unittest.mock import AsyncMock, MagicMock, call, patch

import pytest

from app.notifications.channels.base import NotificationChannel
from app.notifications.channels.email import CC_ADDRESS, EmailChannel, _institution_member_emails
from app.notifications.dispatcher import NotificationDispatcher, notifies
from app.notifications.events import LoginReminderEvent, NoteCreatedEvent, ReminderCreatedEvent
from app.services.email_templates import (
    login_reminder_html,
    reminder_created_html,
)

from .conftest import (
    make_group,
    make_institution,
    make_professor_user,
    make_researcher_user,
    make_user,
)


# ── Eventos ───────────────────────────────────────────────────────────────────

class TestEvents:
    def test_note_created_event(self):
        ev = NoteCreatedEvent(
            note_html="<p>ola</p>",
            profile_user_id=1,
            author_email="a@b.com",
            author_name="A",
            db_factory=lambda: None,
        )
        assert ev.note_html == "<p>ola</p>"
        assert ev.profile_user_id == 1
        assert ev.author_email == "a@b.com"

    def test_reminder_created_event(self):
        ev = ReminderCreatedEvent(
            reminder_html="<p>lembrete</p>",
            reminder_id=42,
            institution_id=5,
            author_email="prof@univ.br",
            author_name="Prof",
            db_factory=lambda: None,
        )
        assert ev.reminder_id == 42
        assert ev.institution_id == 5

    def test_login_reminder_event(self):
        ev = LoginReminderEvent(target_email="x@x.com", target_name="X")
        assert ev.target_email == "x@x.com"
        assert ev.target_name == "X"


# ── NotificationDispatcher ────────────────────────────────────────────────────

class TestNotificationDispatcher:
    def _make_channel(self, handles=True):
        class Ch(NotificationChannel):
            calls = []
            def can_handle(self, t): return handles
            async def handle(self, event): self.calls.append(event)
        return Ch()

    def test_register_adds_channel(self):
        d = NotificationDispatcher()
        d.register(self._make_channel())
        assert len(d._channels) == 1

    def test_dispatch_routes_to_matching_channel(self):
        d = NotificationDispatcher()
        ch = self._make_channel(handles=True)
        d.register(ch)
        ev = LoginReminderEvent("a@a.com", "A")
        asyncio.run(d.dispatch(ev))
        assert ev in ch.calls

    def test_dispatch_skips_non_matching_channel(self):
        d = NotificationDispatcher()
        ch = self._make_channel(handles=False)
        d.register(ch)
        ev = LoginReminderEvent("a@a.com", "A")
        asyncio.run(d.dispatch(ev))
        assert ch.calls == []

    def test_dispatch_calls_all_matching_channels(self):
        d = NotificationDispatcher()
        ch1 = self._make_channel(handles=True)
        ch2 = self._make_channel(handles=True)
        d.register(ch1)
        d.register(ch2)
        ev = LoginReminderEvent("a@a.com", "A")
        asyncio.run(d.dispatch(ev))
        assert ev in ch1.calls
        assert ev in ch2.calls

    def test_dispatch_survives_channel_exception(self):
        class BrokenChannel(NotificationChannel):
            def can_handle(self, t): return True
            async def handle(self, event): raise RuntimeError("boom")

        d = NotificationDispatcher()
        d.register(BrokenChannel())
        ev = LoginReminderEvent("a@a.com", "A")
        # should not raise; asyncio.gather(return_exceptions=True)
        asyncio.run(d.dispatch(ev))

    def test_dispatch_with_no_channels_is_noop(self):
        d = NotificationDispatcher()
        ev = LoginReminderEvent("a@a.com", "A")
        asyncio.run(d.dispatch(ev))  # must not raise


# ── @notifies decorator ───────────────────────────────────────────────────────

class TestNotifiesDecorator:
    def _fresh_dispatcher(self):
        return NotificationDispatcher()

    def test_returns_original_result(self):
        d = NotificationDispatcher()

        @notifies(lambda r, kw: None)
        async def handler():
            return "hello"

        # Patch dispatcher used by the decorator module
        with patch("app.notifications.dispatcher.dispatcher", d):
            async def run():
                return await handler()
            result = asyncio.run(run())
        assert result == "hello"

    def test_fires_event_when_extractor_returns_event(self):
        d = NotificationDispatcher()
        dispatched = []

        async def capture(event):
            dispatched.append(event)

        d.dispatch = capture  # type: ignore

        ev = LoginReminderEvent("a@a.com", "A")

        @notifies(lambda r, kw: ev)
        async def handler():
            return "ok"

        with patch("app.notifications.dispatcher.dispatcher", d):
            async def run():
                result = await handler()
                await asyncio.sleep(0)  # let create_task run
                return result
            asyncio.run(run())

        assert ev in dispatched

    def test_skips_dispatch_when_extractor_returns_none(self):
        d = NotificationDispatcher()
        dispatched = []

        async def capture(event):
            dispatched.append(event)

        d.dispatch = capture  # type: ignore

        @notifies(lambda r, kw: None)
        async def handler():
            return "ok"

        with patch("app.notifications.dispatcher.dispatcher", d):
            async def run():
                await handler()
                await asyncio.sleep(0)
            asyncio.run(run())

        assert dispatched == []

    def test_does_not_propagate_extractor_exception(self):
        d = NotificationDispatcher()

        @notifies(lambda r, kw: 1 / 0)  # ZeroDivisionError
        async def handler():
            return "ok"

        with patch("app.notifications.dispatcher.dispatcher", d):
            async def run():
                return await handler()
            result = asyncio.run(run())

        assert result == "ok"

    def test_wraps_preserves_wrapped_attribute(self):
        @notifies(lambda r, kw: None)
        async def my_func():
            pass

        assert my_func.__wrapped__ is not None or hasattr(my_func, "__wrapped__")


# ── EmailChannel.can_handle ───────────────────────────────────────────────────

class TestEmailChannelCanHandle:
    def setup_method(self):
        self.ch = EmailChannel()

    def test_does_not_handle_note_created_event(self):
        assert not self.ch.can_handle(NoteCreatedEvent)

    def test_handles_reminder_created_event(self):
        assert self.ch.can_handle(ReminderCreatedEvent)

    def test_handles_login_reminder_event(self):
        assert self.ch.can_handle(LoginReminderEvent)

    def test_does_not_handle_unknown_type(self):
        assert not self.ch.can_handle(str)

    def test_handle_routes_reminder_created(self):
        ch = EmailChannel()
        ev = ReminderCreatedEvent("<p>t</p>", 1, None, "a@a.com", "A", lambda: None)

        async def run():
            with patch.object(ch, "_handle_reminder_created", new_callable=AsyncMock) as m:
                await ch.handle(ev)
                m.assert_called_once_with(ev)

        asyncio.run(run())

    def test_handle_routes_login_reminder(self):
        ch = EmailChannel()
        ev = LoginReminderEvent("x@x.com", "X")

        async def run():
            with patch.object(ch, "_handle_login_reminder", new_callable=AsyncMock) as m:
                await ch.handle(ev)
                m.assert_called_once_with(ev)

        asyncio.run(run())


# ── EmailChannel._handle_login_reminder ──────────────────────────────────────

class TestHandleLoginReminder:
    def test_sends_email_to_target(self):
        ch = EmailChannel()
        ev = LoginReminderEvent(target_email="user@test.com", target_name="Fulano")

        async def run():
            with patch("app.notifications.channels.email.send_email", new_callable=AsyncMock) as mock_send:
                await ch._handle_login_reminder(ev)
                mock_send.assert_called_once()
                args = mock_send.call_args
                assert args[0][0] == "user@test.com"

        asyncio.run(run())

    def test_includes_cc_address(self):
        ch = EmailChannel()
        ev = LoginReminderEvent(target_email="user@test.com", target_name="Fulano")

        async def run():
            with patch("app.notifications.channels.email.send_email", new_callable=AsyncMock) as mock_send:
                await ch._handle_login_reminder(ev)
                cc = mock_send.call_args[1].get("cc") or mock_send.call_args[0][3]
                assert CC_ADDRESS in cc

        asyncio.run(run())

    def test_correct_subject(self):
        ch = EmailChannel()
        ev = LoginReminderEvent(target_email="user@test.com", target_name="Fulano")

        async def run():
            with patch("app.notifications.channels.email.send_email", new_callable=AsyncMock) as mock_send:
                await ch._handle_login_reminder(ev)
                subject = mock_send.call_args[0][1]
                assert "falta" in subject.lower() or "alumnus" in subject.lower()

        asyncio.run(run())

    def test_does_not_raise_on_send_failure(self):
        ch = EmailChannel()
        ev = LoginReminderEvent(target_email="user@test.com", target_name="Fulano")

        async def run():
            with patch("app.notifications.channels.email.send_email", side_effect=Exception("network error")):
                await ch._handle_login_reminder(ev)  # must not raise

        asyncio.run(run())


# ── EmailChannel._handle_reminder_created ────────────────────────────────────

class TestHandleReminderCreated:
    def test_sends_to_group_members(self, db, db_factory):
        inst = make_institution(db, name="UFPA Test", domain="ufpatest.br")
        group = make_group(db, name="G1", institution_id=inst.id)
        _, member = make_researcher_user(db, email="member@ufpatest.br", group_id=group.id)

        ev = ReminderCreatedEvent(
            reminder_html="<p>Lembrete</p>",
            reminder_id=1,
            institution_id=inst.id,
            author_email="author@other.com",
            author_name="Author",
            db_factory=db_factory,
        )
        ch = EmailChannel()

        async def run():
            with patch("app.notifications.channels.email.send_email", new_callable=AsyncMock) as mock_send:
                await ch._handle_reminder_created(ev)
                recipients = {c[0][0] for c in mock_send.call_args_list}
                assert "member@ufpatest.br" in recipients

        asyncio.run(run())

    def test_does_not_send_to_author(self, db, db_factory):
        inst = make_institution(db, name="UFPA2", domain="ufpa2.br")
        group = make_group(db, name="G2", institution_id=inst.id)
        _, member = make_researcher_user(db, email="author@ufpa2.br", group_id=group.id)

        ev = ReminderCreatedEvent(
            reminder_html="<p>Lembrete</p>",
            reminder_id=2,
            institution_id=inst.id,
            author_email="author@ufpa2.br",  # autor é membro
            author_name="Author",
            db_factory=db_factory,
        )
        ch = EmailChannel()

        async def run():
            with patch("app.notifications.channels.email.send_email", new_callable=AsyncMock) as mock_send:
                await ch._handle_reminder_created(ev)
                recipients = {c[0][0] for c in mock_send.call_args_list}
                assert "author@ufpa2.br" not in recipients

        asyncio.run(run())

    def test_deduplicates_mention_and_group_member(self, db, db_factory):
        """Pessoa mencionada que também é membro do grupo recebe apenas 1 email."""
        inst = make_institution(db, name="UFPA3", domain="ufpa3.br")
        group = make_group(db, name="G3", institution_id=inst.id)
        _, member = make_researcher_user(db, email="member@ufpa3.br", group_id=group.id)

        note_html = (
            '<p><span data-type="mention" data-id="m" '
            'data-email="member@ufpa3.br">@M</span></p>'
        )
        ev = ReminderCreatedEvent(
            reminder_html=note_html,
            reminder_id=3,
            institution_id=inst.id,
            author_email="other@other.com",
            author_name="Other",
            db_factory=db_factory,
        )
        ch = EmailChannel()

        async def run():
            with patch("app.notifications.channels.email.send_email", new_callable=AsyncMock) as mock_send:
                await ch._handle_reminder_created(ev)
                recipients = [c[0][0] for c in mock_send.call_args_list]
                assert recipients.count("member@ufpa3.br") == 1

        asyncio.run(run())

    def test_skips_when_no_recipients(self, db, db_factory):
        inst = make_institution(db, name="UFPA4", domain="ufpa4.br")

        ev = ReminderCreatedEvent(
            reminder_html="<p>Lembrete vazio</p>",
            reminder_id=4,
            institution_id=inst.id,
            author_email="a@a.com",
            author_name="A",
            db_factory=db_factory,
        )
        ch = EmailChannel()

        async def run():
            with patch("app.notifications.channels.email.send_email", new_callable=AsyncMock) as mock_send:
                await ch._handle_reminder_created(ev)
                mock_send.assert_not_called()

        asyncio.run(run())

    def test_sends_professor_group_members(self, db, db_factory):
        inst = make_institution(db, name="UFPA5", domain="ufpa5.br")
        group = make_group(db, name="G5", institution_id=inst.id)
        _, prof_user = make_professor_user(db, email="profg@ufpa5.br", group_id=group.id)

        ev = ReminderCreatedEvent(
            reminder_html="<p>Lembrete</p>",
            reminder_id=5,
            institution_id=inst.id,
            author_email="other@other.com",
            author_name="Other",
            db_factory=db_factory,
        )
        ch = EmailChannel()

        async def run():
            with patch("app.notifications.channels.email.send_email", new_callable=AsyncMock) as mock_send:
                await ch._handle_reminder_created(ev)
                recipients = {c[0][0] for c in mock_send.call_args_list}
                assert "profg@ufpa5.br" in recipients

        asyncio.run(run())

    def test_no_institution_id_only_sends_to_mentions(self, db, db_factory):
        ev = ReminderCreatedEvent(
            reminder_html='<p><span data-type="mention" data-id="x" data-email="x@x.com">@x</span></p>',
            reminder_id=6,
            institution_id=None,
            author_email="other@other.com",
            author_name="Other",
            db_factory=db_factory,
        )
        ch = EmailChannel()

        async def run():
            with patch("app.notifications.channels.email.send_email", new_callable=AsyncMock) as mock_send:
                await ch._handle_reminder_created(ev)
                recipients = {c[0][0] for c in mock_send.call_args_list}
                assert "x@x.com" in recipients

        asyncio.run(run())


# ── _institution_member_emails ────────────────────────────────────────────────

class TestInstitutionMemberEmails:
    def test_returns_empty_when_no_groups(self, db):
        inst = make_institution(db, name="Empty Uni", domain="empty.br")
        result = _institution_member_emails(db, inst.id)
        assert result == set()

    def test_returns_researcher_emails(self, db):
        inst = make_institution(db, name="Uni R", domain="unir.br")
        group = make_group(db, name="GR", institution_id=inst.id)
        _, u = make_researcher_user(db, email="r@unir.br", group_id=group.id)
        result = _institution_member_emails(db, inst.id)
        assert "r@unir.br" in result

    def test_returns_professor_emails(self, db):
        inst = make_institution(db, name="Uni P", domain="unip.br")
        group = make_group(db, name="GP", institution_id=inst.id)
        _, u = make_professor_user(db, email="p@unip.br", group_id=group.id)
        result = _institution_member_emails(db, inst.id)
        assert "p@unip.br" in result

    def test_excludes_inactive_users(self, db):
        inst = make_institution(db, name="Uni Inativo", domain="inactive.br")
        group = make_group(db, name="GI", institution_id=inst.id)
        _, u = make_researcher_user(db, email="inactive@inactive.br", group_id=group.id, ativo=False)
        result = _institution_member_emails(db, inst.id)
        assert "inactive@inactive.br" not in result


# ── email_templates ───────────────────────────────────────────────────────────

class TestEmailTemplates:
    def test_reminder_created_contains_creator_name(self):
        html = reminder_created_html("João Silva", "<p>fazer algo</p>")
        assert "João Silva" in html

    def test_reminder_created_contains_cta_link_to_reminders(self):
        html = reminder_created_html("A", "<p>x</p>")
        assert "/app/reminders" in html

    def test_reminder_created_excerpt_from_html(self):
        html = reminder_created_html("A", "<p>conteúdo do lembrete</p>")
        assert "conteúdo do lembrete" in html

    def test_login_reminder_contains_user_name(self):
        html = login_reminder_html("Maria Souza")
        assert "Maria Souza" in html

    def test_login_reminder_contains_quem_nao_aparece(self):
        html = login_reminder_html("Alguém")
        assert "quem não aparece" in html.lower() or "quem nao aparece" in html.lower()

    def test_login_reminder_contains_cta_link(self):
        html = login_reminder_html("X")
        assert "alumnus.gustavopinto.org" in html

    def test_login_reminder_headline_is_firm(self):
        html = login_reminder_html("X")
        # Não deve ter linguagem suave
        assert "sentimos sua falta" not in html.lower()


# ── email_service ─────────────────────────────────────────────────────────────

class TestEmailService:
    def test_skips_when_no_api_key(self):
        import resend
        from app.services.email_service import send_email

        async def run():
            with patch("app.services.email_service.resend") as mock_resend:
                mock_resend.api_key = ""
                mock_resend.Emails = MagicMock()
                await send_email("a@a.com", "Test", "<p>html</p>")
                mock_resend.Emails.send.assert_not_called()

        asyncio.run(run())

    def test_sends_with_cc_in_params(self):
        from app.services.email_service import _send_sync

        with patch("app.services.email_service.resend") as mock_resend:
            mock_resend.Emails.send = MagicMock()
            _send_sync("a@a.com", "Subject", "<p>html</p>", cc=["cc@cc.com"])
            call_params = mock_resend.Emails.send.call_args[0][0]
            assert call_params["cc"] == ["cc@cc.com"]

    def test_sends_without_cc_when_none(self):
        from app.services.email_service import _send_sync

        with patch("app.services.email_service.resend") as mock_resend:
            mock_resend.Emails.send = MagicMock()
            _send_sync("a@a.com", "Subject", "<p>html</p>")
            call_params = mock_resend.Emails.send.call_args[0][0]
            assert "cc" not in call_params

    def test_from_address_is_noreply(self):
        from app.services.email_service import FROM_ADDRESS
        assert "noreply@alumnus.gustavopinto.org" in FROM_ADDRESS

    def test_send_email_does_not_raise_on_resend_exception(self):
        from app.services.email_service import send_email

        async def run():
            with patch("app.services.email_service.asyncio.to_thread", side_effect=Exception("timeout")):
                with patch("app.services.email_service.resend") as mr:
                    mr.api_key = "key"
                    await send_email("a@a.com", "Sub", "<p>html</p>")  # must not raise

        asyncio.run(run())

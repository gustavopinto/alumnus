import asyncio
import logging

from sqlalchemy.orm import Session

from ...models import Professor, ProfessorGroup, Researcher, ResearchGroup, User
from ...services.email_service import send_email
from ...services.email_templates import (
    login_reminder_html,
    mention_html,
    note_created_html,
    reminder_created_html,
)
from ...services.mention_parser import extract_mentions, resolve_mention_emails
from ...slug import slugify
from ..events import LoginReminderEvent, NoteCreatedEvent, ReminderCreatedEvent
from .base import NotificationChannel

logger = logging.getLogger(__name__)

CC_ADDRESS = "gpinto@ufpa.br"


class EmailChannel(NotificationChannel):
    def can_handle(self, event_type: type) -> bool:
        return event_type in {NoteCreatedEvent, ReminderCreatedEvent, LoginReminderEvent}

    async def handle(self, event) -> None:
        if isinstance(event, NoteCreatedEvent):
            await self._handle_note_created(event)
        elif isinstance(event, ReminderCreatedEvent):
            await self._handle_reminder_created(event)
        elif isinstance(event, LoginReminderEvent):
            await self._handle_login_reminder(event)

    async def _handle_note_created(self, event: NoteCreatedEvent) -> None:
        db: Session = event.db_factory()
        try:
            profile_user = db.query(User).get(event.profile_user_id)
            if not profile_user:
                return

            profile_slug = slugify(profile_user.nome)
            profile_email = profile_user.email

            researcher = (
                db.query(Researcher).filter(Researcher.id == profile_user.researcher_id).first()
                if profile_user.researcher_id else None
            )
            group_id = researcher.group_id if researcher else None

            mentions = extract_mentions(event.note_html)
            mention_emails = resolve_mention_emails(db, mentions, group_id, event.author_email)

            tasks = []
            if profile_email and profile_email != event.author_email and profile_email not in mention_emails:
                tasks.append((
                    profile_email,
                    "Nova anotação no seu perfil",
                    note_created_html(event.author_name, event.note_html, profile_slug),
                ))
            for email in mention_emails:
                tasks.append((
                    email,
                    "Oba! Você foi marcado no Alumnus!",
                    mention_html(event.author_name, event.note_html, profile_user.nome, profile_slug),
                ))
            if tasks:
                await asyncio.gather(*[
                    send_email(to, subject, html, cc=[CC_ADDRESS])
                    for to, subject, html in tasks
                ])
        except Exception:
            logger.exception("Erro ao enviar notificações de nota")
        finally:
            db.close()

    async def _handle_reminder_created(self, event: ReminderCreatedEvent) -> None:
        db: Session = event.db_factory()
        try:
            mentions = extract_mentions(event.reminder_html)
            mention_emails = resolve_mention_emails(db, mentions, None, event.author_email)

            group_emails: set[str] = set()
            if event.institution_id:
                group_emails = _institution_member_emails(db, event.institution_id)

            # União com deduplicação: mencionados + membros do grupo, sem o autor
            all_emails = mention_emails | group_emails
            if event.author_email:
                all_emails.discard(event.author_email)

            if not all_emails:
                return

            html = reminder_created_html(event.author_name, event.reminder_html)
            await asyncio.gather(*[
                send_email(email, "Novo lembrete no Alumnus", html, cc=[CC_ADDRESS])
                for email in all_emails
            ])
        except Exception:
            logger.exception("Erro ao enviar notificações de lembrete")
        finally:
            db.close()

    async def _handle_login_reminder(self, event: LoginReminderEvent) -> None:
        try:
            html = login_reminder_html(event.target_name, event.days_inactive)
            await send_email(
                event.target_email,
                f"Alumnus: {event.target_name}, você sumiu.",
                html,
                cc=[CC_ADDRESS],
            )
        except Exception:
            logger.exception("Erro ao enviar lembrete de login para %s", event.target_email)


def _institution_member_emails(db: Session, institution_id: int) -> set[str]:
    group_ids = [
        row[0] for row in
        db.query(ResearchGroup.id).filter(ResearchGroup.institution_id == institution_id).all()
    ]
    if not group_ids:
        return set()

    emails: set[str] = set()
    for row in (
        db.query(User.email)
        .join(Researcher, User.researcher_id == Researcher.id)
        .filter(Researcher.group_id.in_(group_ids), User.ativo == True)
        .all()
    ):
        if row[0]:
            emails.add(row[0])
    for row in (
        db.query(User.email)
        .join(Professor, User.professor_id == Professor.id)
        .join(ProfessorGroup, ProfessorGroup.professor_id == Professor.id)
        .filter(ProfessorGroup.group_id.in_(group_ids), User.ativo == True)
        .all()
    ):
        if row[0]:
            emails.add(row[0])
    return emails

from dataclasses import dataclass
from typing import Any


@dataclass
class NoteCreatedEvent:
    note_html: str
    profile_user_id: int
    author_email: str | None
    author_name: str
    db_factory: Any


@dataclass
class ReminderCreatedEvent:
    reminder_html: str
    reminder_id: int
    institution_id: int | None
    author_email: str | None
    author_name: str
    db_factory: Any


@dataclass
class LoginReminderEvent:
    target_email: str
    target_name: str
    days_inactive: int | None = None

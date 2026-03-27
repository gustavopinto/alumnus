"""
Unit tests for app/services/reminder_service.py

Covers:
- reminder_to_out
- list_ordered / list_reminders_out
- create (with and without mentions)
- get_by_id
- update
- can_user_delete_reminder
- delete
- single_reminder_out
"""

from datetime import date, datetime, timedelta
from unittest.mock import patch

import pytest

from app.services import reminder_service
from app.schemas import ReminderCreate, ReminderUpdate
from app.models import Reminder, User, Researcher

from .conftest import make_researcher, make_user, make_reminder


# ---------------------------------------------------------------------------
# reminder_to_out
# ---------------------------------------------------------------------------

class TestReminderToOut:
    def test_basic_reminder_without_creator(self, db):
        reminder = make_reminder(db, text="Simples")
        out = reminder_service.reminder_to_out(reminder, viewer_id=None)

        assert out.id == reminder.id
        assert out.text == "Simples"
        assert out.done is False
        assert out.created_by_name is None

    def test_includes_creator_name_from_loaded_relationship(self, db):
        user = make_user(db, email="creator@univ.edu.br", nome="Criador Nome")
        reminder = make_reminder(db, text="Com criador", created_by_id=user.id)
        # simulate eager-loaded relationship
        reminder.created_by = user

        out = reminder_service.reminder_to_out(reminder, viewer_id=user.id)
        assert out.created_by_name == "Criador Nome"
        assert out.created_by_id == user.id

    def test_uses_creator_name_map_when_relationship_not_loaded(self, db):
        user = make_user(db, email="map@univ.edu.br", nome="Mapeado")
        reminder = make_reminder(db, text="Via mapa", created_by_id=user.id)
        reminder.created_by = None  # relationship not loaded

        name_map = {user.id: "Mapeado"}
        out = reminder_service.reminder_to_out(reminder, viewer_id=None, creator_name_map=name_map)
        assert out.created_by_name == "Mapeado"

    def test_created_by_name_none_when_no_map_and_no_relationship(self, db):
        user = make_user(db, email="nomap@univ.edu.br", nome="Sem mapa")
        reminder = make_reminder(db, text="Sem mapa", created_by_id=user.id)
        reminder.created_by = None

        out = reminder_service.reminder_to_out(reminder, viewer_id=None, creator_name_map=None)
        assert out.created_by_name is None

    def test_due_date_is_preserved(self, db):
        d = date(2025, 12, 31)
        reminder = make_reminder(db, text="Com data", due_date=d)
        out = reminder_service.reminder_to_out(reminder, viewer_id=None)
        assert out.due_date == d


# ---------------------------------------------------------------------------
# list_ordered
# ---------------------------------------------------------------------------

class TestListOrdered:
    def test_returns_empty_list_when_no_reminders(self, db):
        assert reminder_service.list_ordered(db) == []

    def test_done_reminders_sorted_after_pending(self, db):
        make_reminder(db, text="Feito", done=True)
        make_reminder(db, text="Pendente", done=False)

        results = reminder_service.list_ordered(db)
        texts = [r.text for r in results]
        assert texts.index("Pendente") < texts.index("Feito")

    def test_pending_sorted_by_due_date_asc(self, db):
        later_date = date(2025, 6, 15)
        earlier_date = date(2025, 3, 1)
        make_reminder(db, text="Tarde", due_date=later_date)
        make_reminder(db, text="Cedo", due_date=earlier_date)

        results = reminder_service.list_ordered(db)
        pending = [r for r in results if not r.done]
        assert pending[0].text == "Cedo"
        assert pending[1].text == "Tarde"

    def test_nulls_last_for_due_date(self, db):
        make_reminder(db, text="Sem data", due_date=None)
        make_reminder(db, text="Com data", due_date=date(2025, 1, 1))

        results = reminder_service.list_ordered(db)
        pending = [r for r in results if not r.done]
        assert pending[0].text == "Com data"
        assert pending[-1].text == "Sem data"


# ---------------------------------------------------------------------------
# list_reminders_out
# ---------------------------------------------------------------------------

class TestListRemindersOut:
    def test_returns_list_of_reminder_out(self, db):
        make_reminder(db, text="Um")
        make_reminder(db, text="Dois")

        results = reminder_service.list_reminders_out(db, viewer_id=None)
        assert len(results) == 2

    def test_creator_name_resolved_from_db(self, db):
        user = make_user(db, email="lista@univ.edu.br", nome="Lista User")
        make_reminder(db, text="Com user", created_by_id=user.id)

        results = reminder_service.list_reminders_out(db, viewer_id=user.id)
        assert len(results) == 1
        # name should be resolved even if not eager-loaded
        assert results[0].created_by_name is not None

    def test_empty_db_returns_empty_list(self, db):
        results = reminder_service.list_reminders_out(db, viewer_id=None)
        assert results == []


# ---------------------------------------------------------------------------
# create
# ---------------------------------------------------------------------------

class TestCreate:
    def test_creates_and_returns_reminder(self, db):
        data = ReminderCreate(text="Novo lembrete", due_date=None)
        reminder = reminder_service.create(db, data, created_by_id=None)

        assert reminder.id is not None
        assert reminder.text == "Novo lembrete"
        assert reminder.done is False

    def test_reminder_persisted_to_db(self, db):
        data = ReminderCreate(text="Persistido")
        reminder = reminder_service.create(db, data, created_by_id=None)

        fetched = db.query(Reminder).filter(Reminder.id == reminder.id).first()
        assert fetched is not None

    def test_due_date_stored_correctly(self, db):
        d = date(2025, 9, 30)
        data = ReminderCreate(text="Com prazo", due_date=d)
        reminder = reminder_service.create(db, data, created_by_id=None)

        assert reminder.due_date == d

    def test_no_mention_copies_when_no_created_by(self, db):
        data = ReminderCreate(text="@ana lembrete sem user")
        reminder_service.create(db, data, created_by_id=None)

        total = db.query(Reminder).count()
        assert total == 1

    def test_creates_single_reminder_with_mention_text(self, db):
        creator = make_user(db, email="creator@univ.edu.br", nome="Creator", role="professor")

        data = ReminderCreate(text="@ana-silva revise o prazo")
        reminder_service.create(db, data, created_by_id=creator.id)

        total = db.query(Reminder).count()
        assert total == 1

    def test_creates_reminder_with_institution_id(self, db):
        creator = make_user(db, email="inst@univ.edu.br", nome="Prof", role="professor")

        data = ReminderCreate(text="Lembrete institucional", institution_id=None)
        reminder = reminder_service.create(db, data, created_by_id=creator.id)

        assert reminder.created_by_id == creator.id


# ---------------------------------------------------------------------------
# get_by_id
# ---------------------------------------------------------------------------

class TestGetById:
    def test_returns_reminder_when_found(self, db):
        reminder = make_reminder(db, text="Busca por id")
        fetched = reminder_service.get_by_id(db, reminder.id)
        assert fetched is not None
        assert fetched.id == reminder.id

    def test_returns_none_for_nonexistent_id(self, db):
        assert reminder_service.get_by_id(db, 99999) is None


# ---------------------------------------------------------------------------
# update
# ---------------------------------------------------------------------------

class TestUpdate:
    def test_updates_text(self, db):
        reminder = make_reminder(db, text="Original")
        data = ReminderUpdate(text="Atualizado")
        updated = reminder_service.update(db, reminder, data)
        assert updated.text == "Atualizado"

    def test_updates_done_flag(self, db):
        reminder = make_reminder(db, done=False)
        data = ReminderUpdate(done=True)
        updated = reminder_service.update(db, reminder, data)
        assert updated.done is True

    def test_updates_due_date(self, db):
        reminder = make_reminder(db)
        new_date = date(2025, 11, 11)
        data = ReminderUpdate(due_date=new_date)
        updated = reminder_service.update(db, reminder, data)
        assert updated.due_date == new_date

    def test_partial_update_preserves_other_fields(self, db):
        reminder = make_reminder(db, text="Preservar", due_date=date(2025, 1, 1))
        data = ReminderUpdate(done=True)
        updated = reminder_service.update(db, reminder, data)
        assert updated.text == "Preservar"
        assert updated.due_date == date(2025, 1, 1)


# ---------------------------------------------------------------------------
# can_user_delete_reminder
# ---------------------------------------------------------------------------

class TestCanUserDeleteReminder:
    def test_professor_can_delete_any_reminder(self, db):
        professor = make_user(db, email="prof@univ.edu.br", role="professor")
        other = make_user(db, email="other@univ.edu.br", role="researcher")
        reminder = make_reminder(db, created_by_id=other.id)

        assert reminder_service.can_user_delete_reminder(professor, reminder) is True

    def test_admin_can_delete_any_reminder(self, db):
        admin = make_user(db, email="admin@univ.edu.br", role="admin")
        other = make_user(db, email="s@univ.edu.br", role="researcher")
        reminder = make_reminder(db, created_by_id=other.id)

        assert reminder_service.can_user_delete_reminder(admin, reminder) is True

    def test_superadmin_can_delete_any_reminder(self, db):
        superadmin = make_user(db, email="sa@univ.edu.br", role="superadmin")
        other = make_user(db, email="s2@univ.edu.br", role="researcher")
        reminder = make_reminder(db, created_by_id=other.id)

        assert reminder_service.can_user_delete_reminder(superadmin, reminder) is True

    def test_student_can_delete_own_reminder(self, db):
        student = make_user(db, email="st@univ.edu.br", role="researcher")
        reminder = make_reminder(db, created_by_id=student.id)

        assert reminder_service.can_user_delete_reminder(student, reminder) is True

    def test_student_cannot_delete_others_reminder(self, db):
        student = make_user(db, email="st2@univ.edu.br", role="researcher")
        other = make_user(db, email="other2@univ.edu.br", role="researcher")
        reminder = make_reminder(db, created_by_id=other.id)

        assert reminder_service.can_user_delete_reminder(student, reminder) is False

    def test_student_cannot_delete_reminder_with_no_creator(self, db):
        student = make_user(db, email="st3@univ.edu.br", role="researcher")
        reminder = make_reminder(db, created_by_id=None)

        assert reminder_service.can_user_delete_reminder(student, reminder) is False


# ---------------------------------------------------------------------------
# delete
# ---------------------------------------------------------------------------

class TestDelete:
    def test_deletes_reminder_from_db(self, db):
        reminder = make_reminder(db, text="Deletar")
        reminder_id = reminder.id

        reminder_service.delete(db, reminder)

        assert db.query(Reminder).filter(Reminder.id == reminder_id).first() is None


# ---------------------------------------------------------------------------
# single_reminder_out
# ---------------------------------------------------------------------------

class TestSingleReminderOut:
    def test_returns_none_for_nonexistent_id(self, db):
        result = reminder_service.single_reminder_out(db, 99999, viewer_id=None)
        assert result is None

    def test_returns_reminder_out_for_existing_reminder(self, db):
        reminder = make_reminder(db, text="Single out")
        result = reminder_service.single_reminder_out(db, reminder.id, viewer_id=None)

        assert result is not None
        assert result.id == reminder.id
        assert result.text == "Single out"

    def test_resolves_creator_name(self, db):
        user = make_user(db, email="single@univ.edu.br", nome="Single Creator")
        reminder = make_reminder(db, text="Com criador", created_by_id=user.id)

        result = reminder_service.single_reminder_out(db, reminder.id, viewer_id=None)
        assert result is not None
        assert result.created_by_name == "Single Creator"

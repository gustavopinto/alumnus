"""
Unit tests for app/schemas.py validators.

Covers field_validators on:
- UserProfileUpdate (instagram_url, twitter_url)
- RegisterRequest (email normalization, password length)
"""

import pytest
from datetime import date
from pydantic import ValidationError

from app.schemas import UserProfileUpdate, RegisterRequest, ReminderCreate, ReminderUpdate


# ---------------------------------------------------------------------------
# UserProfileUpdate.validate_instagram_handle
# ---------------------------------------------------------------------------

class TestInstagramHandleValidator:
    def test_valid_handle_without_at(self):
        obj = UserProfileUpdate(instagram_url="joao.silva")
        assert obj.instagram_url == "joao.silva"

    def test_valid_handle_with_at_prefix_is_stripped(self):
        obj = UserProfileUpdate(instagram_url="@joao.silva")
        assert obj.instagram_url == "joao.silva"

    def test_none_is_accepted(self):
        obj = UserProfileUpdate(instagram_url=None)
        assert obj.instagram_url is None

    def test_empty_string_becomes_none(self):
        obj = UserProfileUpdate(instagram_url="")
        assert obj.instagram_url is None

    def test_whitespace_only_becomes_none(self):
        obj = UserProfileUpdate(instagram_url="   ")
        assert obj.instagram_url is None

    def test_handle_with_dots_and_underscores(self):
        obj = UserProfileUpdate(instagram_url="my.handle_123")
        assert obj.instagram_url == "my.handle_123"

    def test_handle_31_chars_raises(self):
        long_handle = "a" * 31  # exceeds 30 char limit
        with pytest.raises(ValidationError) as exc_info:
            UserProfileUpdate(instagram_url=long_handle)
        assert "Instagram" in str(exc_info.value)

    def test_handle_with_invalid_char_raises(self):
        with pytest.raises(ValidationError) as exc_info:
            UserProfileUpdate(instagram_url="invalid handle!")
        assert "Instagram" in str(exc_info.value)

    def test_handle_with_hyphen_raises(self):
        with pytest.raises(ValidationError):
            UserProfileUpdate(instagram_url="invalid-handle")

    def test_handle_exactly_30_chars_accepted(self):
        handle = "a" * 30
        obj = UserProfileUpdate(instagram_url=handle)
        assert obj.instagram_url == handle

    def test_handle_exactly_1_char_accepted(self):
        obj = UserProfileUpdate(instagram_url="a")
        assert obj.instagram_url == "a"

    def test_at_prefix_stripped_then_validated(self):
        # "@" + 30 valid chars = total string 31 chars, but after stripping @ it is 30 — valid
        handle = "@" + "a" * 30
        obj = UserProfileUpdate(instagram_url=handle)
        assert obj.instagram_url == "a" * 30


# ---------------------------------------------------------------------------
# UserProfileUpdate.validate_twitter_handle
# ---------------------------------------------------------------------------

class TestTwitterHandleValidator:
    def test_valid_handle_without_at(self):
        obj = UserProfileUpdate(twitter_url="joao_silva")
        assert obj.twitter_url == "joao_silva"

    def test_valid_handle_with_at_prefix_is_stripped(self):
        obj = UserProfileUpdate(twitter_url="@joao_silva")
        assert obj.twitter_url == "joao_silva"

    def test_none_is_accepted(self):
        obj = UserProfileUpdate(twitter_url=None)
        assert obj.twitter_url is None

    def test_empty_string_becomes_none(self):
        obj = UserProfileUpdate(twitter_url="")
        assert obj.twitter_url is None

    def test_whitespace_only_becomes_none(self):
        obj = UserProfileUpdate(twitter_url="   ")
        assert obj.twitter_url is None

    def test_handle_16_chars_raises(self):
        long_handle = "a" * 16  # exceeds 15 char limit
        with pytest.raises(ValidationError) as exc_info:
            UserProfileUpdate(twitter_url=long_handle)
        assert "Twitter" in str(exc_info.value)

    def test_handle_exactly_15_chars_accepted(self):
        handle = "a" * 15
        obj = UserProfileUpdate(twitter_url=handle)
        assert obj.twitter_url == handle

    def test_handle_with_dot_raises(self):
        # dots are not allowed in Twitter handles
        with pytest.raises(ValidationError):
            UserProfileUpdate(twitter_url="user.name")

    def test_handle_with_hyphen_raises(self):
        with pytest.raises(ValidationError):
            UserProfileUpdate(twitter_url="user-name")

    def test_alphanumeric_and_underscore_accepted(self):
        obj = UserProfileUpdate(twitter_url="User_123")
        assert obj.twitter_url == "User_123"

    def test_at_prefix_stripped_then_validated(self):
        handle = "@" + "a" * 15
        obj = UserProfileUpdate(twitter_url=handle)
        assert obj.twitter_url == "a" * 15


# ---------------------------------------------------------------------------
# RegisterRequest validators
# ---------------------------------------------------------------------------

class TestRegisterRequestValidators:
    def test_email_is_normalized_to_lowercase(self):
        req = RegisterRequest(email="User@UNIV.EDU.BR", password="password123")
        assert req.email == "user@univ.edu.br"

    def test_email_strips_whitespace(self):
        req = RegisterRequest(email="  user@univ.edu.br  ", password="password123")
        assert req.email == "user@univ.edu.br"

    def test_email_normalize_empty_string(self):
        req = RegisterRequest(email="", password="password123")
        assert req.email == ""

    def test_password_min_length_8_accepted(self):
        req = RegisterRequest(email="a@b.com", password="12345678")
        assert req.password == "12345678"

    def test_password_exactly_8_chars_accepted(self):
        req = RegisterRequest(email="a@b.com", password="abcdefgh")
        assert len(req.password) == 8

    def test_password_7_chars_raises(self):
        with pytest.raises(ValidationError) as exc_info:
            RegisterRequest(email="a@b.com", password="1234567")
        assert "8 caracter" in str(exc_info.value)

    def test_password_empty_raises(self):
        with pytest.raises(ValidationError):
            RegisterRequest(email="a@b.com", password="")

    def test_long_password_accepted(self):
        req = RegisterRequest(email="a@b.com", password="a" * 100)
        assert len(req.password) == 100


# ---------------------------------------------------------------------------
# ReminderCreate / ReminderUpdate basic validation
# ---------------------------------------------------------------------------

class TestReminderSchemas:
    def test_reminder_create_with_text_only(self):
        r = ReminderCreate(text="Lembrete simples")
        assert r.text == "Lembrete simples"
        assert r.due_date is None

    def test_reminder_create_with_due_date(self):
        d = date(2025, 6, 1)
        r = ReminderCreate(text="Com data", due_date=d)
        assert r.due_date == d

    def test_reminder_update_partial(self):
        r = ReminderUpdate(done=True)
        assert r.done is True
        assert r.text is None
        assert r.due_date is None

    def test_reminder_update_all_fields(self):
        d = date(2025, 7, 4)
        r = ReminderUpdate(text="Novo texto", due_date=d, done=False)
        assert r.text == "Novo texto"
        assert r.due_date == d
        assert r.done is False

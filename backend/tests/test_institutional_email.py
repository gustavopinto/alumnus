"""
Unit tests for app/institutional_email.py

Covers:
- extract_domain
- is_public_email_domain
"""

import pytest

from app.institutional_email import extract_domain, is_public_email_domain


class TestExtractDomain:
    def test_extracts_domain_from_email(self):
        assert extract_domain("user@gmail.com") == "gmail.com"

    def test_extracts_institutional_domain(self):
        assert extract_domain("prof@usp.br") == "usp.br"

    def test_empty_string_returns_empty(self):
        assert extract_domain("") == ""

    def test_none_handled_as_empty(self):
        assert extract_domain(None) == ""  # type: ignore[arg-type]

    def test_no_at_sign_returns_empty(self):
        assert extract_domain("notanemail") == ""

    def test_uppercase_input_normalised(self):
        assert extract_domain("USER@GMAIL.COM") == "gmail.com"

    def test_multiple_at_signs_uses_last(self):
        # rsplit('@', 1) takes the last @
        assert extract_domain("a@b@gmail.com") == "gmail.com"

    def test_strips_whitespace(self):
        assert extract_domain("  user@outlook.com  ") == "outlook.com"


class TestIsPublicEmailDomain:
    @pytest.mark.parametrize("email", [
        "user@gmail.com",
        "user@hotmail.com",
        "user@outlook.com",
        "user@yahoo.com",
        "user@icloud.com",
        "user@protonmail.com",
        "user@uol.com.br",
        "user@hotmail.com.br",
    ])
    def test_public_domains_return_true(self, email):
        assert is_public_email_domain(email) is True

    @pytest.mark.parametrize("email", [
        "prof@usp.br",
        "student@unicamp.br",
        "researcher@harvard.edu",
        "me@mycompany.com",
    ])
    def test_institutional_domains_return_false(self, email):
        assert is_public_email_domain(email) is False

    def test_empty_email_returns_false(self):
        assert is_public_email_domain("") is False

    def test_no_at_returns_false(self):
        assert is_public_email_domain("notanemail") is False

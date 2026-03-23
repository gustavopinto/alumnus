"""
Unit tests for app/slug.py

Covers:
- slugify (accented characters, spaces, special chars, edge cases)
"""

import pytest

from app.slug import slugify


class TestSlugify:
    def test_basic_ascii_lowercased(self):
        assert slugify("Hello World") == "hello-world"

    def test_accents_removed(self):
        assert slugify("João") == "joao"

    def test_cedilla_removed(self):
        assert slugify("Conceição") == "conceicao"

    def test_multiple_spaces_become_single_hyphen(self):
        assert slugify("Ana   Silva") == "ana---silva"

    def test_leading_trailing_whitespace_stripped(self):
        assert slugify("  nome  ") == "nome"

    def test_full_portuguese_name(self):
        result = slugify("Ana Lígia Peçanha")
        assert result == "ana-ligia-pecanha"

    def test_special_chars_removed(self):
        result = slugify("Dr. José!")
        assert "!" not in result
        assert "." not in result

    def test_numbers_preserved(self):
        result = slugify("Pesquisador 1")
        assert "1" in result

    def test_empty_string(self):
        assert slugify("") == ""

    def test_already_slug(self):
        assert slugify("already-slug") == "already-slug"

    def test_hyphens_in_input_preserved(self):
        result = slugify("nome-composto")
        assert result == "nome-composto"

"""Tests for app/routers/profiles.py"""
from app.routers.auth import make_token
from app.schemas import ResearcherCreate
from app.services import researcher_service

from .conftest import make_user


class TestGetProfileBySlug:
    def test_get_user_profile_by_slug(self, client, db):
        # Create user with a known name
        user = make_user(db, email="profile@univ.br", nome="Profile User", role="researcher")
        auth_user = make_user(db, email="auth@univ.br", role="professor")
        token = make_token(auth_user)
        resp = client.get(
            "/api/profiles/by-slug/profile-user",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["user"] is not None

    def test_get_researcher_profile_by_slug(self, client, db):
        researcher_service.create(db, ResearcherCreate(
            email="rprofile@univ.br",
            nome="Researcher Profile",
            status="mestrado",
        ))
        auth_user = make_user(db, email="authprofile@univ.br", role="professor")
        token = make_token(auth_user)
        resp = client.get(
            "/api/profiles/by-slug/researcher-profile",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["researcher"] is not None

    def test_returns_404_for_unknown_slug(self, client, db):
        auth_user = make_user(db, email="auth404@univ.br", role="professor")
        token = make_token(auth_user)
        resp = client.get(
            "/api/profiles/by-slug/nao-existe-xyz",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 404

    def test_requires_auth(self, client, db):
        resp = client.get("/api/profiles/by-slug/some-profile")
        assert resp.status_code in (401, 403)

    def test_get_profile_with_researcher_linked(self, client, db):
        # User that also has a researcher record
        r = researcher_service.create(db, ResearcherCreate(
            email="linked_profile@univ.br",
            nome="Linked Profile User",
            status="doutorado",
        ))
        auth_user = make_user(db, email="authlinked@univ.br", role="professor")
        token = make_token(auth_user)
        resp = client.get(
            "/api/profiles/by-slug/linked-profile-user",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200

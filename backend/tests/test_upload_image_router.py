"""Tests for POST /api/upload/image"""
import io

from PIL import Image as PILImage

from app.routers.auth import make_token

from .conftest import make_user


def make_png_bytes():
    buf = io.BytesIO()
    img = PILImage.new('RGB', (10, 10), color='red')
    img.save(buf, format='PNG')
    return buf.getvalue()


class TestUploadImage:
    def test_upload_success_returns_url(self, client, db):
        user = make_user(db, email="imgupload@univ.br", role="researcher")
        token = make_token(user)
        png = make_png_bytes()
        resp = client.post(
            "/api/upload/image",
            files={"file": ("test.png", png, "image/png")},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "url" in data
        assert isinstance(data["url"], str)
        assert len(data["url"]) > 0

    def test_unauthenticated_returns_401_or_403(self, client, db):
        png = make_png_bytes()
        resp = client.post(
            "/api/upload/image",
            files={"file": ("test.png", png, "image/png")},
        )
        assert resp.status_code in (401, 403)

"""
Testes para a refatoração photo_url/photo_thumb_url → photo_file_id/photo_thumb_file_id.

Cobre:
- _store_bytes retorna int (não tupla)
- Propriedades User.photo_url e User.photo_thumb_url derivadas da FK
- save_researcher_photo retorna (int, int)
- POST /upload/photo retorna file_id/thumb_file_id (não URLs)
- PATCH /users/me e /users/{id} aceitam photo_file_id/photo_thumb_file_id
- Campos antigos photo_url/photo_thumb_url não são mais aceitos como input
"""
import asyncio
import io

import pytest
from PIL import Image
from fastapi import UploadFile
from unittest.mock import AsyncMock

from app.fileutils import _store_bytes
from app.models import FileUpload, User
from app.routers.auth import make_token
from app.services import upload_service

from .conftest import make_user


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_jpeg_bytes(width: int = 100, height: int = 100) -> bytes:
    img = Image.new("RGB", (width, height), color=(100, 150, 200))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()


def _make_upload_file(content: bytes, filename: str = "photo.jpg") -> UploadFile:
    upload = AsyncMock(spec=UploadFile)
    upload.read = AsyncMock(return_value=content)
    upload.filename = filename
    return upload


def _create_file_upload(db, content: bytes = b"fake", mime: str = "image/jpeg") -> FileUpload:
    record = FileUpload(data=content, mime_type=mime, original_name="test.jpg")
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


# ---------------------------------------------------------------------------
# _store_bytes retorna int
# ---------------------------------------------------------------------------

class TestStoreBytesReturnsInt:
    def test_returns_integer_id(self, db):
        result = _store_bytes(db, b"data", "image/jpeg", "test.jpg")
        assert isinstance(result, int)
        assert result > 0

    def test_cria_registro_no_banco(self, db):
        fid = _store_bytes(db, b"conteudo", "image/jpeg", "img.jpg")
        record = db.get(FileUpload, fid)
        assert record is not None
        assert record.data == b"conteudo"
        assert record.mime_type == "image/jpeg"

    def test_ids_distintos_para_cada_chamada(self, db):
        id1 = _store_bytes(db, b"a", "image/jpeg", "a.jpg")
        id2 = _store_bytes(db, b"b", "image/jpeg", "b.jpg")
        assert id1 != id2


# ---------------------------------------------------------------------------
# Propriedades User.photo_url e User.photo_thumb_url
# ---------------------------------------------------------------------------

class TestUserPhotoProperties:
    def test_photo_url_none_sem_fk(self, db):
        user = make_user(db, email="nophoto@test.br")
        assert user.photo_url is None

    def test_photo_thumb_url_none_sem_fk(self, db):
        user = make_user(db, email="nothumb@test.br")
        assert user.photo_thumb_url is None

    def test_photo_url_derivada_do_file_id(self, db):
        f = _create_file_upload(db)
        user = make_user(db, email="withphoto@test.br")
        user.photo_file_id = f.id
        db.commit()
        db.refresh(user)
        assert user.photo_url == f"/api/files/{f.id}"

    def test_photo_thumb_url_derivada_do_thumb_file_id(self, db):
        f = _create_file_upload(db)
        user = make_user(db, email="withthumb@test.br")
        user.photo_thumb_file_id = f.id
        db.commit()
        db.refresh(user)
        assert user.photo_thumb_url == f"/api/files/{f.id}"

    def test_photo_url_e_thumb_url_independentes(self, db):
        f1 = _create_file_upload(db, b"main")
        f2 = _create_file_upload(db, b"thumb")
        user = make_user(db, email="bothphoto@test.br")
        user.photo_file_id = f1.id
        user.photo_thumb_file_id = f2.id
        db.commit()
        db.refresh(user)
        assert user.photo_url == f"/api/files/{f1.id}"
        assert user.photo_thumb_url == f"/api/files/{f2.id}"
        assert user.photo_url != user.photo_thumb_url


# ---------------------------------------------------------------------------
# save_researcher_photo retorna (int, int)
# ---------------------------------------------------------------------------

class TestSaveResearcherPhoto:
    def test_retorna_dois_inteiros(self, db):
        jpeg = _make_jpeg_bytes()
        upload = _make_upload_file(jpeg, "foto.jpg")
        file_id, thumb_file_id = asyncio.run(
            upload_service.save_researcher_photo(upload, db)
        )
        assert isinstance(file_id, int)
        assert isinstance(thumb_file_id, int)

    def test_cria_dois_registros_distintos(self, db):
        jpeg = _make_jpeg_bytes()
        upload = _make_upload_file(jpeg, "foto.jpg")
        file_id, thumb_file_id = asyncio.run(
            upload_service.save_researcher_photo(upload, db)
        )
        assert file_id != thumb_file_id
        assert db.get(FileUpload, file_id) is not None
        assert db.get(FileUpload, thumb_file_id) is not None

    def test_rejeita_pdf(self, db):
        from fastapi import HTTPException
        upload = _make_upload_file(b"%PDF-1.4", "doc.pdf")
        with pytest.raises(HTTPException) as exc_info:
            asyncio.run(upload_service.save_researcher_photo(upload, db))
        assert exc_info.value.status_code == 415

    def test_rejeita_arquivo_grande(self, db):
        from fastapi import HTTPException
        big = b"x" * (6 * 1024 * 1024)
        upload = _make_upload_file(big, "big.jpg")
        with pytest.raises(HTTPException) as exc_info:
            asyncio.run(upload_service.save_researcher_photo(upload, db))
        assert exc_info.value.status_code == 413


# ---------------------------------------------------------------------------
# POST /upload/photo — resposta com file_id / thumb_file_id (não URLs)
# ---------------------------------------------------------------------------

class TestUploadPhotoEndpoint:
    def test_retorna_file_id_e_thumb_file_id(self, client, db):
        jpeg = _make_jpeg_bytes()
        resp = client.post(
            "/api/upload/photo",
            files={"file": ("photo.jpg", jpeg, "image/jpeg")},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert "file_id" in body
        assert "thumb_file_id" in body
        assert isinstance(body["file_id"], int)
        assert isinstance(body["thumb_file_id"], int)

    def test_nao_retorna_url_diretamente(self, client, db):
        jpeg = _make_jpeg_bytes()
        resp = client.post(
            "/api/upload/photo",
            files={"file": ("photo.jpg", jpeg, "image/jpeg")},
        )
        body = resp.json()
        assert "url" not in body
        assert "thumb_url" not in body

    def test_ids_correspondem_a_registros_existentes(self, client, db):
        jpeg = _make_jpeg_bytes()
        resp = client.post(
            "/api/upload/photo",
            files={"file": ("photo.jpg", jpeg, "image/jpeg")},
        )
        body = resp.json()
        assert db.get(FileUpload, body["file_id"]) is not None
        assert db.get(FileUpload, body["thumb_file_id"]) is not None

    def test_rejeita_pdf(self, client, db):
        resp = client.post(
            "/api/upload/photo",
            files={"file": ("doc.pdf", b"%PDF-1.4", "application/pdf")},
        )
        assert resp.status_code == 415


# ---------------------------------------------------------------------------
# PATCH /users/me com photo_file_id / photo_thumb_file_id
# ---------------------------------------------------------------------------

class TestUpdateMyProfilePhotoFields:
    def test_atualiza_photo_file_id(self, client, db):
        f = _create_file_upload(db)
        user = make_user(db, email="mephoto@test.br")
        token = make_token(user)
        resp = client.patch(
            "/api/users/me",
            json={"photo_file_id": f.id},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["photo_url"] == f"/api/files/{f.id}"

    def test_atualiza_photo_thumb_file_id(self, client, db):
        f = _create_file_upload(db)
        user = make_user(db, email="methumb@test.br")
        token = make_token(user)
        resp = client.patch(
            "/api/users/me",
            json={"photo_thumb_file_id": f.id},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["photo_thumb_url"] == f"/api/files/{f.id}"

    def test_photo_url_nulo_sem_foto(self, client, db):
        user = make_user(db, email="menulphoto@test.br")
        token = make_token(user)
        resp = client.patch(
            "/api/users/me",
            json={"bio": "sem foto"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["photo_url"] is None
        assert body["photo_thumb_url"] is None

    def test_campo_antigo_photo_url_como_string_ignorado(self, client, db):
        """photo_url como string não deve ser aceito no schema de entrada."""
        user = make_user(db, email="oldurl@test.br")
        token = make_token(user)
        resp = client.patch(
            "/api/users/me",
            json={"photo_url": "http://example.com/old.jpg"},
            headers={"Authorization": f"Bearer {token}"},
        )
        # Pydantic ignora campos extras por padrão; photo_url não deve ser salvo como string
        assert resp.status_code == 200
        db.refresh(user)
        # O campo photo_file_id deve continuar None (não foi setado)
        assert user.photo_file_id is None


# ---------------------------------------------------------------------------
# PATCH /users/{id} com photo_file_id / photo_thumb_file_id
# ---------------------------------------------------------------------------

class TestUpdateUserProfilePhotoFields:
    def test_professor_atualiza_foto_de_researcher(self, client, db):
        f = _create_file_upload(db)
        prof = make_user(db, email="profphoto@test.br", role="professor")
        target = make_user(db, email="resphoto@test.br", role="researcher")
        token = make_token(prof)
        resp = client.patch(
            f"/api/users/{target.id}",
            json={"photo_file_id": f.id, "photo_thumb_file_id": f.id},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["photo_url"] == f"/api/files/{f.id}"
        assert body["photo_thumb_url"] == f"/api/files/{f.id}"

    def test_photo_url_na_resposta_usa_formato_correto(self, client, db):
        f = _create_file_upload(db)
        user = make_user(db, email="urlformat@test.br", role="researcher")
        token = make_token(user)
        resp = client.patch(
            f"/api/users/{user.id}",
            json={"photo_file_id": f.id},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["photo_url"].startswith("/api/files/")

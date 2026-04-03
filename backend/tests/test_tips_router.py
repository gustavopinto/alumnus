"""Tests for app/routers/tips.py"""
from app.routers.auth import make_token
from app.schemas import TipCreate
from app.services import tip_service

from .conftest import make_user


class TestListTips:
    def test_list_tips_empty(self, client, db):
        user = make_user(db, email="listips@univ.br", role="researcher")
        token = make_token(user)
        resp = client.get("/api/tips/", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_list_tips_with_data(self, client, db):
        user = make_user(db, email="listtips2@univ.br", role="researcher")
        token = make_token(user)
        tip_service.create_tip(db, TipCreate(question="Q Listed", answer="A Listed"), user.id)
        resp = client.get("/api/tips/", headers={"Authorization": f"Bearer {token}"})
        assert len(resp.json()) >= 1

    def test_requires_auth(self, client, db):
        resp = client.get("/api/tips/")
        assert resp.status_code in (401, 403)


class TestCreateTip:
    def test_creates_tip(self, client, db):
        user = make_user(db, email="createtip@univ.br", role="researcher")
        token = make_token(user)
        resp = client.post(
            "/api/tips/",
            json={"question": "Como funciona?", "answer": "Assim funciona!"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["question"] == "Como funciona?"
        assert resp.json()["answer"] == "Assim funciona!"


class TestDeleteTip:
    def test_author_can_delete(self, client, db):
        user = make_user(db, email="deltip@univ.br", role="researcher")
        token = make_token(user)
        tip = tip_service.create_tip(db, TipCreate(question="Del?", answer="Del!"), user.id)
        resp = client.delete(f"/api/tips/{tip.id}", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200

    def test_professor_can_delete_any(self, client, db):
        researcher = make_user(db, email="tipresearcher@univ.br", role="researcher")
        prof = make_user(db, email="tipprof@univ.br", role="professor")
        tip = tip_service.create_tip(db, TipCreate(question="Q Prof Del", answer="A"), researcher.id)
        token = make_token(prof)
        resp = client.delete(f"/api/tips/{tip.id}", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200

    def test_returns_404_for_unknown(self, client, db):
        user = make_user(db, email="deltip404@univ.br", role="researcher")
        token = make_token(user)
        resp = client.delete("/api/tips/9999", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 404

    def test_non_author_cannot_delete(self, client, db):
        author = make_user(db, email="tipauthor@univ.br", role="researcher")
        other = make_user(db, email="tipother@univ.br", role="researcher")
        tip = tip_service.create_tip(db, TipCreate(question="Q?", answer="A!"), author.id)
        token = make_token(other)
        resp = client.delete(f"/api/tips/{tip.id}", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 403


class TestToggleVote:
    def test_toggle_vote_adds(self, client, db):
        user = make_user(db, email="votetip@univ.br", role="researcher")
        token = make_token(user)
        tip = tip_service.create_tip(db, TipCreate(question="Vote?", answer="Yes!"), user.id)
        resp = client.post(f"/api/tips/{tip.id}/vote", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        assert resp.json()["voted"] is True
        assert resp.json()["vote_count"] == 1

    def test_toggle_vote_removes(self, client, db):
        user = make_user(db, email="unvotetip@univ.br", role="researcher")
        token = make_token(user)
        tip = tip_service.create_tip(db, TipCreate(question="Unvote?", answer="Yes!"), user.id)
        client.post(f"/api/tips/{tip.id}/vote", headers={"Authorization": f"Bearer {token}"})
        resp = client.post(f"/api/tips/{tip.id}/vote", headers={"Authorization": f"Bearer {token}"})
        assert resp.json()["voted"] is False
        assert resp.json()["vote_count"] == 0

    def test_vote_404_for_unknown(self, client, db):
        user = make_user(db, email="vote404@univ.br", role="researcher")
        token = make_token(user)
        resp = client.post("/api/tips/9999/vote", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 404


class TestAddComment:
    def test_adds_comment(self, client, db):
        user = make_user(db, email="commenttip@univ.br", role="researcher")
        token = make_token(user)
        tip = tip_service.create_tip(db, TipCreate(question="Comment?", answer="Yes!"), user.id)
        resp = client.post(
            f"/api/tips/{tip.id}/comments",
            json={"text": "Meu comentario"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["text"] == "Meu comentario"

    def test_comment_404_for_unknown_tip(self, client, db):
        user = make_user(db, email="comment404@univ.br", role="researcher")
        token = make_token(user)
        resp = client.post("/api/tips/9999/comments", json={"text": "x"}, headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 404


class TestDeleteComment:
    def test_author_can_delete_comment(self, client, db):
        user = make_user(db, email="delcommenttip@univ.br", role="researcher")
        token = make_token(user)
        tip = tip_service.create_tip(db, TipCreate(question="DelC?", answer="DelC!"), user.id)
        comment = tip_service.add_comment(db, tip.id, "Para deletar", user.id)
        resp = client.delete(f"/api/tips/comments/{comment.id}", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200

    def test_comment_404_for_unknown(self, client, db):
        user = make_user(db, email="delcomment404@univ.br", role="researcher")
        token = make_token(user)
        resp = client.delete("/api/tips/comments/9999", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 404

    def test_non_author_cannot_delete_comment(self, client, db):
        author = make_user(db, email="commentauth@univ.br", role="researcher")
        other = make_user(db, email="commentother@univ.br", role="researcher")
        tip = tip_service.create_tip(db, TipCreate(question="Q", answer="A"), author.id)
        comment = tip_service.add_comment(db, tip.id, "Comentario", author.id)
        token = make_token(other)
        resp = client.delete(f"/api/tips/comments/{comment.id}", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 403


class TestCreateTipWithHtml:
    def test_stores_html_content(self, client, db):
        user = make_user(db, email="htmltip@univ.br", role="researcher")
        token = make_token(user)
        html_answer = '<p>Resposta com <strong>negrito</strong></p>'
        resp = client.post(
            "/api/tips/",
            json={"question": "HTML Q?", "answer": html_answer},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["answer"] == html_answer

    def test_stores_mention_html(self, client, db):
        user = make_user(db, email="mentiontip@univ.br", role="researcher")
        token = make_token(user)
        html = '<p>Ver com <span data-type="mention" data-id="gustavo-pinto" class="mention">@Gustavo Pinto</span></p>'
        resp = client.post(
            "/api/tips/",
            json={"question": "Mention Q?", "answer": html},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        assert 'data-type="mention"' in resp.json()["answer"]

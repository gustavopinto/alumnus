"""Tests for app/services/tip_service.py"""
import pytest
from passlib.context import CryptContext

from app.models import Institution, User
from app.schemas import TipCreate
from app.services import tip_service

pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")


def make_user(db, email="tip@test.br"):
    u = User(
        email=email,
        nome="Tip User",
        password_hash=pwd_ctx.hash("pass"),
        role="researcher",
    )
    db.add(u)
    db.commit()
    db.refresh(u)
    return u


def make_institution(db, name="TIPINST", domain="tipinst.br"):
    inst = Institution(name=name, domain=domain)
    db.add(inst)
    db.commit()
    db.refresh(inst)
    return inst


class TestCreateTip:
    def test_creates_tip(self, db):
        u = make_user(db)
        data = TipCreate(question="Como funciona?", answer="Assim funciona.")
        tip = tip_service.create_tip(db, data, u.id)
        assert tip.id is not None
        assert tip.question == "Como funciona?"
        assert tip.answer == "Assim funciona."
        assert tip.author_id == u.id

    def test_creates_tip_with_institution(self, db):
        u = make_user(db, "tipinst@test.br")
        inst = make_institution(db)
        data = TipCreate(question="Q?", answer="A.", institution_id=inst.id)
        tip = tip_service.create_tip(db, data, u.id)
        assert tip.institution_id == inst.id

    def test_default_position_is_zero(self, db):
        u = make_user(db, "tippos@test.br")
        tip = tip_service.create_tip(db, TipCreate(question="Q", answer="A"), u.id)
        assert tip.position == 0


class TestListTips:
    def test_returns_all_tips(self, db):
        u = make_user(db, "listip@test.br")
        tip_service.create_tip(db, TipCreate(question="Q1", answer="A1"), u.id)
        tip_service.create_tip(db, TipCreate(question="Q2", answer="A2"), u.id)
        tips = tip_service.list_tips(db)
        assert len(tips) >= 2

    def test_filters_by_institution(self, db):
        u = make_user(db, "listipinst@test.br")
        inst = make_institution(db, "LISTINST", "listinst.br")
        tip_service.create_tip(db, TipCreate(question="Q Inst", answer="A Inst", institution_id=inst.id), u.id)
        tip_service.create_tip(db, TipCreate(question="Q Global", answer="A Global"), u.id)
        tips = tip_service.list_tips(db, institution_id=inst.id)
        assert len(tips) == 1
        assert tips[0].question == "Q Inst"

    def test_sorted_by_votes_desc(self, db):
        u = make_user(db, "sortvotes@test.br")
        tip1 = tip_service.create_tip(db, TipCreate(question="Q1 Sort", answer="A1"), u.id)
        tip2 = tip_service.create_tip(db, TipCreate(question="Q2 Sort", answer="A2"), u.id)
        tip_service.toggle_vote(db, tip2, u.id)
        tips = tip_service.list_tips(db)
        # tip2 has 1 vote so should come before tip1
        tip_ids = [t.id for t in tips]
        assert tip_ids.index(tip2.id) < tip_ids.index(tip1.id)


class TestGetTip:
    def test_returns_tip(self, db):
        u = make_user(db, "gettip@test.br")
        tip = tip_service.create_tip(db, TipCreate(question="Get?", answer="Get!"), u.id)
        found = tip_service.get_tip(db, tip.id)
        assert found is not None
        assert found.id == tip.id

    def test_returns_none_for_unknown(self, db):
        assert tip_service.get_tip(db, 9999) is None


class TestDeleteTip:
    def test_deletes_tip(self, db):
        u = make_user(db, "deltip@test.br")
        tip = tip_service.create_tip(db, TipCreate(question="Del?", answer="Del!"), u.id)
        tip_id = tip.id
        tip_service.delete_tip(db, tip)
        assert tip_service.get_tip(db, tip_id) is None


class TestToggleVote:
    def test_vote_adds_vote(self, db):
        u = make_user(db, "vote@test.br")
        tip = tip_service.create_tip(db, TipCreate(question="Vote?", answer="Vote!"), u.id)
        voted, count = tip_service.toggle_vote(db, tip, u.id)
        assert voted is True
        assert count == 1

    def test_vote_toggles_off(self, db):
        u = make_user(db, "unvote@test.br")
        tip = tip_service.create_tip(db, TipCreate(question="Unvote?", answer="Unvote!"), u.id)
        tip_service.toggle_vote(db, tip, u.id)
        voted, count = tip_service.toggle_vote(db, tip, u.id)
        assert voted is False
        assert count == 0

    def test_multiple_users_can_vote(self, db):
        u1 = make_user(db, "vote1@test.br")
        u2 = make_user(db, "vote2@test.br")
        tip = tip_service.create_tip(db, TipCreate(question="Multi Vote?", answer="Yes!"), u1.id)
        tip_service.toggle_vote(db, tip, u1.id)
        _, count = tip_service.toggle_vote(db, tip, u2.id)
        assert count == 2


class TestAddComment:
    def test_adds_comment(self, db):
        u = make_user(db, "comment@test.br")
        tip = tip_service.create_tip(db, TipCreate(question="Comment?", answer="Comment!"), u.id)
        comment = tip_service.add_comment(db, tip.id, "Meu comentario", u.id)
        assert comment.id is not None
        assert comment.text == "Meu comentario"
        assert comment.author_id == u.id
        assert comment.entry_id == tip.id


class TestGetTipComment:
    def test_returns_comment(self, db):
        u = make_user(db, "getcomment@test.br")
        tip = tip_service.create_tip(db, TipCreate(question="Q", answer="A"), u.id)
        comment = tip_service.add_comment(db, tip.id, "Texto", u.id)
        found = tip_service.get_tip_comment(db, comment.id)
        assert found is not None
        assert found.id == comment.id

    def test_returns_none_for_unknown(self, db):
        assert tip_service.get_tip_comment(db, 9999) is None


class TestDeleteComment:
    def test_deletes_comment(self, db):
        u = make_user(db, "delcomment@test.br")
        tip = tip_service.create_tip(db, TipCreate(question="DelC?", answer="DelC!"), u.id)
        comment = tip_service.add_comment(db, tip.id, "Para deletar", u.id)
        comment_id = comment.id
        tip_service.delete_tip_comment(db, comment)
        assert tip_service.get_tip_comment(db, comment_id) is None

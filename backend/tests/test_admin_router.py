"""
Unit tests for app/routers/admin.py

Uses the TestClient with an in-memory SQLite DB.
Auth dependencies are overridden with helpers that inject a preset user.

Covers:
- GET  /admin/stats
- GET  /admin/users
- PUT  /admin/users/{user_id}
- DELETE /admin/users/{user_id}
- POST /admin/bulk-delete
- DELETE /admin/researchers/{researcher_id}
"""

from datetime import datetime

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.deps import require_dashboard, require_superadmin
from app.database import get_db
from app.models import (
    User,
    Researcher,
    Institution,
    Professor,
    ProfessorInstitution,
    ResearchGroup,
)

from .conftest import make_user, make_researcher, make_reminder


# ---------------------------------------------------------------------------
# Helper: override a dependency with a fixed user
# ---------------------------------------------------------------------------

def _override_deps(db_session, acting_user: User):
    """Return a dict of overrides that inject db_session and acting_user."""

    def _get_db():
        yield db_session

    def _require_dashboard():
        return acting_user

    def _require_superadmin():
        return acting_user

    return {
        get_db: _get_db,
        require_dashboard: _require_dashboard,
        require_superadmin: _require_superadmin,
    }


@pytest.fixture
def superadmin_client(db):
    sa = make_user(db, email="sa@univ.edu.br", nome="Super Admin", role="superadmin")
    app.dependency_overrides.update(_override_deps(db, sa))
    with TestClient(app, raise_server_exceptions=True) as c:
        yield c, sa, db
    app.dependency_overrides.clear()


@pytest.fixture
def professor_client(db):
    prof = make_user(db, email="prof@univ.edu.br", nome="Professor", role="professor")
    app.dependency_overrides.update(_override_deps(db, prof))
    with TestClient(app, raise_server_exceptions=True) as c:
        yield c, prof, db
    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# GET /admin/stats
# ---------------------------------------------------------------------------

class TestGetStats:
    def test_superadmin_sees_all_role_counts(self, superadmin_client):
        client, sa, db = superadmin_client
        # Add another user of a different role
        make_user(db, email="s@univ.edu.br", role="student")

        resp = client.get("/admin/stats")
        assert resp.status_code == 200
        body = resp.json()
        assert "users_by_role" in body
        assert "total_researchers" in body
        assert "total_reminders" in body

    def test_professor_sees_stats_without_superadmin_count(self, professor_client):
        client, prof, db = professor_client
        resp = client.get("/admin/stats")
        assert resp.status_code == 200
        body = resp.json()
        # superadmin count hidden
        assert body["users_by_role"]["superadmin"] == 0

    def test_stats_counts_reminders(self, superadmin_client):
        client, sa, db = superadmin_client
        make_reminder(db, text="R1")
        make_reminder(db, text="R2")

        resp = client.get("/admin/stats")
        assert resp.json()["total_reminders"] == 2

    def test_stats_counts_researchers(self, superadmin_client):
        client, sa, db = superadmin_client
        make_researcher(db, nome="Dr. X", email="drx@univ.edu.br", ativo=True)

        resp = client.get("/admin/stats")
        assert resp.json()["total_researchers"] >= 1


# ---------------------------------------------------------------------------
# GET /admin/users
# ---------------------------------------------------------------------------

class TestListUsers:
    def test_returns_list_with_registered_users(self, superadmin_client):
        client, sa, db = superadmin_client
        make_user(db, email="u1@univ.edu.br")

        resp = client.get("/admin/users")
        assert resp.status_code == 200
        emails = [u["email"] for u in resp.json()]
        assert "sa@univ.edu.br" in emails
        assert "u1@univ.edu.br" in emails

    def test_pending_researchers_included(self, superadmin_client):
        client, sa, db = superadmin_client
        make_researcher(db, nome="Pendente X", email="pending@univ.edu.br", registered=False, ativo=True)

        resp = client.get("/admin/users")
        assert resp.status_code == 200
        names = [u["nome"] for u in resp.json()]
        assert "Pendente X" in names

    def test_professor_excludes_pure_superadmin(self, professor_client):
        client, prof, db = professor_client
        # superadmin without researcher_id should be excluded for professor view
        sa = make_user(db, email="puresu@univ.edu.br", role="superadmin")

        resp = client.get("/admin/users")
        assert resp.status_code == 200
        emails = [u["email"] for u in resp.json()]
        assert "puresu@univ.edu.br" not in emails

    def test_superadmin_with_researcher_included_for_professor(self, professor_client):
        client, prof, db = professor_client
        researcher = make_researcher(db, nome="SA com pesq", email="saresearch@univ.edu.br")
        make_user(
            db,
            email="saresearch@univ.edu.br",
            role="superadmin",
            researcher_id=researcher.id,
        )

        resp = client.get("/admin/users")
        assert resp.status_code == 200
        emails = [u["email"] for u in resp.json()]
        assert "saresearch@univ.edu.br" in emails

    def test_professor_sees_only_users_from_linked_institutions(self, professor_client):
        client, acting_user, db = professor_client

        prof = Professor(nome="Prof Dashboard")
        db.add(prof)
        db.flush()
        acting_user.professor_id = prof.id

        inst_a = Institution(name="Inst A", domain="insta.edu.br")
        inst_b = Institution(name="Inst B", domain="instb.edu.br")
        db.add_all([inst_a, inst_b])
        db.flush()

        db.add(
            ProfessorInstitution(
                professor_id=prof.id,
                institution_id=inst_a.id,
                institutional_email="prof@insta.edu.br",
            )
        )

        # Aluno da instituição vinculada (deve aparecer)
        group_a = ResearchGroup(name="GA", institution_id=inst_a.id)
        db.add(group_a)
        db.flush()
        res_a = Researcher(nome="Aluno A", status="mestrado", email="alunoa@insta.edu.br", group_id=group_a.id, ativo=True, registered=True)
        db.add(res_a)
        db.flush()
        make_user(db, email="alunoa@insta.edu.br", nome="Aluno A", role="student", researcher_id=res_a.id)

        # Aluno de outra instituição (não deve aparecer)
        group_b = ResearchGroup(name="GB", institution_id=inst_b.id)
        db.add(group_b)
        db.flush()
        res_b = Researcher(nome="Aluno B", status="mestrado", email="alunob@instb.edu.br", group_id=group_b.id, ativo=True, registered=True)
        db.add(res_b)
        db.flush()
        make_user(db, email="alunob@instb.edu.br", nome="Aluno B", role="student", researcher_id=res_b.id)

        db.commit()

        resp = client.get("/admin/users")
        assert resp.status_code == 200
        emails = [u["email"] for u in resp.json()]
        assert "alunoa@insta.edu.br" in emails
        assert "alunob@instb.edu.br" not in emails

    def test_professor_with_multiple_institutions_sees_both(self, professor_client):
        client, acting_user, db = professor_client

        prof = Professor(nome="Prof Multi")
        db.add(prof)
        db.flush()
        acting_user.professor_id = prof.id

        inst_a = Institution(name="Inst M1", domain="m1.edu.br")
        inst_b = Institution(name="Inst M2", domain="m2.edu.br")
        db.add_all([inst_a, inst_b])
        db.flush()

        db.add_all(
            [
                ProfessorInstitution(
                    professor_id=prof.id,
                    institution_id=inst_a.id,
                    institutional_email="prof.m1@m1.edu.br",
                ),
                ProfessorInstitution(
                    professor_id=prof.id,
                    institution_id=inst_b.id,
                    institutional_email="prof.m2@m2.edu.br",
                ),
            ]
        )

        group_a = ResearchGroup(name="GM1", institution_id=inst_a.id)
        group_b = ResearchGroup(name="GM2", institution_id=inst_b.id)
        db.add_all([group_a, group_b])
        db.flush()

        res_a = Researcher(nome="Aluno M1", status="mestrado", email="aluno.m1@m1.edu.br", group_id=group_a.id, ativo=True, registered=True)
        res_b = Researcher(nome="Aluno M2", status="mestrado", email="aluno.m2@m2.edu.br", group_id=group_b.id, ativo=True, registered=True)
        db.add_all([res_a, res_b])
        db.flush()

        make_user(db, email="aluno.m1@m1.edu.br", nome="Aluno M1", role="student", researcher_id=res_a.id)
        make_user(db, email="aluno.m2@m2.edu.br", nome="Aluno M2", role="student", researcher_id=res_b.id)

        db.commit()

        resp = client.get("/admin/users")
        assert resp.status_code == 200
        emails = [u["email"] for u in resp.json()]
        assert "aluno.m1@m1.edu.br" in emails
        assert "aluno.m2@m2.edu.br" in emails

    def test_response_sorted_superadmin_first(self, superadmin_client):
        client, sa, db = superadmin_client
        make_user(db, email="z_student@univ.edu.br", role="student")

        resp = client.get("/admin/users")
        users = resp.json()
        # filter out pending rows (id=None)
        real_users = [u for u in users if u.get("id") is not None]
        roles = [u["role"] for u in real_users]
        # superadmin should appear before student
        if "superadmin" in roles and "student" in roles:
            assert roles.index("superadmin") < roles.index("student")


# ---------------------------------------------------------------------------
# PUT /admin/users/{user_id}
# ---------------------------------------------------------------------------

class TestUpdateUser:
    def test_superadmin_can_update_another_users_role(self, superadmin_client):
        client, sa, db = superadmin_client
        student = make_user(db, email="target@univ.edu.br", role="student")

        resp = client.put(f"/admin/users/{student.id}", json={"role": "professor"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["role"] == "professor"

    def test_cannot_update_own_role(self, superadmin_client):
        client, sa, db = superadmin_client
        resp = client.put(f"/admin/users/{sa.id}", json={"role": "student"})
        assert resp.status_code == 400

    def test_invalid_role_returns_400(self, superadmin_client):
        client, sa, db = superadmin_client
        other = make_user(db, email="other@univ.edu.br", role="student")
        resp = client.put(f"/admin/users/{other.id}", json={"role": "invalid_role"})
        assert resp.status_code == 400

    def test_nonexistent_user_returns_404(self, superadmin_client):
        client, sa, db = superadmin_client
        resp = client.put("/admin/users/99999", json={"role": "student"})
        assert resp.status_code == 404

    def test_promotion_to_professor_sets_plan_defaults(self, superadmin_client):
        client, sa, db = superadmin_client
        student = make_user(db, email="promote@univ.edu.br", role="student")

        resp = client.put(f"/admin/users/{student.id}", json={"role": "professor"})
        assert resp.status_code == 200
        db.refresh(student)
        assert student.plan_type == "trial"

    def test_demotion_to_student_clears_plan(self, superadmin_client):
        client, sa, db = superadmin_client
        prof = make_user(
            db,
            email="demote@univ.edu.br",
            role="professor",
            plan_type="trial",
            plan_status="active",
        )

        resp = client.put(f"/admin/users/{prof.id}", json={"role": "student"})
        assert resp.status_code == 200
        db.refresh(prof)
        assert prof.plan_type is None

    def test_is_admin_set_for_admin_role(self, superadmin_client):
        client, sa, db = superadmin_client
        student = make_user(db, email="toadmin@univ.edu.br", role="student")

        resp = client.put(f"/admin/users/{student.id}", json={"role": "admin"})
        assert resp.status_code == 200
        db.refresh(student)
        assert student.is_admin is True


# ---------------------------------------------------------------------------
# DELETE /admin/users/{user_id}
# ---------------------------------------------------------------------------

class TestDeleteUser:
    def test_superadmin_can_delete_student(self, superadmin_client):
        client, sa, db = superadmin_client
        student = make_user(db, email="del@univ.edu.br", role="student")

        resp = client.delete(f"/admin/users/{student.id}")
        assert resp.status_code == 204

        assert db.query(User).filter(User.id == student.id).first() is None

    def test_cannot_delete_own_account(self, superadmin_client):
        client, sa, db = superadmin_client
        resp = client.delete(f"/admin/users/{sa.id}")
        assert resp.status_code == 400

    def test_nonexistent_user_returns_404(self, superadmin_client):
        client, sa, db = superadmin_client
        resp = client.delete("/admin/users/99999")
        assert resp.status_code == 404

    def test_professor_cannot_delete_superadmin(self, professor_client):
        client, prof, db = professor_client
        # professor_client uses require_dashboard — the check is inside the handler
        sa_user = make_user(db, email="protected@univ.edu.br", role="superadmin")

        resp = client.delete(f"/admin/users/{sa_user.id}")
        assert resp.status_code == 403

    def test_deleting_user_marks_researcher_inactive(self, superadmin_client):
        client, sa, db = superadmin_client
        researcher = make_researcher(db, nome="R del", email="rdel@univ.edu.br", registered=True)
        student = make_user(
            db, email="rdel@univ.edu.br", role="student", researcher_id=researcher.id
        )

        client.delete(f"/admin/users/{student.id}")
        db.refresh(researcher)
        assert researcher.ativo is False
        assert researcher.registered is False


# ---------------------------------------------------------------------------
# POST /admin/bulk-delete
# ---------------------------------------------------------------------------

class TestBulkDelete:
    def test_bulk_delete_users(self, superadmin_client):
        client, sa, db = superadmin_client
        u1 = make_user(db, email="bd1@univ.edu.br", role="student")
        u2 = make_user(db, email="bd2@univ.edu.br", role="student")

        resp = client.post("/admin/bulk-delete", json={"user_ids": [u1.id, u2.id], "researcher_ids": []})
        assert resp.status_code == 204
        assert db.query(User).filter(User.id == u1.id).first() is None
        assert db.query(User).filter(User.id == u2.id).first() is None

    def test_bulk_delete_skips_own_id(self, superadmin_client):
        client, sa, db = superadmin_client

        resp = client.post("/admin/bulk-delete", json={"user_ids": [sa.id], "researcher_ids": []})
        assert resp.status_code == 204
        # self should not be deleted
        assert db.query(User).filter(User.id == sa.id).first() is not None

    def test_bulk_delete_unregistered_researchers(self, superadmin_client):
        client, sa, db = superadmin_client
        r = make_researcher(db, nome="Pending R", email="pr@univ.edu.br", registered=False)

        resp = client.post("/admin/bulk-delete", json={"user_ids": [], "researcher_ids": [r.id]})
        assert resp.status_code == 204
        assert db.query(Researcher).filter(Researcher.id == r.id).first() is None

    def test_bulk_delete_skips_registered_researchers(self, superadmin_client):
        client, sa, db = superadmin_client
        r = make_researcher(db, nome="Reg R", email="regr@univ.edu.br", registered=True)

        resp = client.post("/admin/bulk-delete", json={"user_ids": [], "researcher_ids": [r.id]})
        assert resp.status_code == 204
        # registered researcher should NOT be deleted via this route
        assert db.query(Researcher).filter(Researcher.id == r.id).first() is not None

    def test_bulk_delete_does_not_delete_superadmin_when_caller_is_professor(self, professor_client):
        client, prof, db = professor_client
        sa_user = make_user(db, email="sabd@univ.edu.br", role="superadmin")

        resp = client.post("/admin/bulk-delete", json={"user_ids": [sa_user.id], "researcher_ids": []})
        assert resp.status_code == 204
        assert db.query(User).filter(User.id == sa_user.id).first() is not None


# ---------------------------------------------------------------------------
# DELETE /admin/researchers/{researcher_id}
# ---------------------------------------------------------------------------

class TestDeletePendingResearcher:
    def test_deletes_unregistered_researcher(self, superadmin_client):
        client, sa, db = superadmin_client
        r = make_researcher(db, nome="Pendente", email="pend@univ.edu.br", registered=False)

        resp = client.delete(f"/admin/researchers/{r.id}")
        assert resp.status_code == 204
        assert db.query(Researcher).filter(Researcher.id == r.id).first() is None

    def test_404_for_nonexistent_researcher(self, superadmin_client):
        client, sa, db = superadmin_client
        resp = client.delete("/admin/researchers/99999")
        assert resp.status_code == 404

    def test_400_when_researcher_already_registered(self, superadmin_client):
        client, sa, db = superadmin_client
        r = make_researcher(db, nome="Cadastrado", email="cad@univ.edu.br", registered=True)

        resp = client.delete(f"/admin/researchers/{r.id}")
        assert resp.status_code == 400

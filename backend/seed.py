#!/usr/bin/env python3
"""
Cria usuários iniciais no banco (superadmin + professor).
Criar um professor sempre cria também: Professor, Institution, ProfessorInstitution, ResearchGroup, ProfessorGroup.

Uso:
  python seed.py
  python seed.py postgresql://...

Variáveis de ambiente (opcional):
  SEED_SUPERADMIN_EMAIL, SEED_SUPERADMIN_PASSWORD, SEED_SUPERADMIN_NOME
  SEED_PROFESSOR_EMAIL, SEED_PROFESSOR_PASSWORD, SEED_PROFESSOR_NOME
"""

import json
import os
import sys

import psycopg2
from passlib.context import CryptContext

pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")

SUPERADMIN_EMAIL    = os.getenv("SEED_SUPERADMIN_EMAIL",    "admin@alumnus.app")
SUPERADMIN_PASSWORD = os.getenv("SEED_SUPERADMIN_PASSWORD", "changeme123")
SUPERADMIN_NOME     = os.getenv("SEED_SUPERADMIN_NOME",     "Superadmin")

PROFESSOR_EMAIL    = os.getenv("SEED_PROFESSOR_EMAIL",    "professor@alumnus.app")
PROFESSOR_PASSWORD = os.getenv("SEED_PROFESSOR_PASSWORD", "changeme123")
PROFESSOR_NOME     = os.getenv("SEED_PROFESSOR_NOME",     "Professor")


def get_url():
    if len(sys.argv) > 1 and not sys.argv[1].startswith("--"):
        return sys.argv[1]
    url = os.getenv("DATABASE_URL", "")
    if not url:
        sys.exit("Erro: DATABASE_URL não definida.")
    return url.replace("postgres://", "postgresql://", 1)


def upsert_superadmin(cur, email, nome, password):
    cur.execute("SELECT id FROM users WHERE email = %s", (email,))
    if cur.fetchone():
        print(f"  Já existe: {email} — sem alteração.")
        return
    h = pwd_ctx.hash(password)
    cur.execute(
        "INSERT INTO users (email, nome, password_hash, role, is_admin) VALUES (%s,%s,%s,%s,%s) RETURNING id",
        (email, nome, h, "superadmin", True),
    )
    print(f"  Criado superadmin: {email}  id={cur.fetchone()[0]}")


def upsert_professor(cur, email, nome, password):
    # 1. Institution (always upsert)
    domain = email.split("@")[-1]
    inst_name = domain.split(".")[0].upper()
    cur.execute(
        "INSERT INTO institutions (name, domain) VALUES (%s,%s) ON CONFLICT (domain) DO NOTHING RETURNING id",
        (inst_name, domain),
    )
    row = cur.fetchone()
    if row:
        institution_id = row[0]
    else:
        cur.execute("SELECT id FROM institutions WHERE domain = %s", (domain,))
        institution_id = cur.fetchone()[0]

    # Check if user already exists
    cur.execute("SELECT id, professor_id FROM users WHERE email = %s", (email,))
    existing = cur.fetchone()
    if existing:
        user_id, professor_id = existing
        print(f"  Usuário já existe: {email}  user_id={user_id}  professor_id={professor_id}")
    else:
        # 2. Professor
        cur.execute(
            "INSERT INTO professors (nome, ativo) VALUES (%s, TRUE) RETURNING id",
            (nome,),
        )
        professor_id = cur.fetchone()[0]

        # 3. User
        h = pwd_ctx.hash(password)
        cur.execute(
            "INSERT INTO users (email, nome, password_hash, role, is_admin, professor_id) VALUES (%s,%s,%s,%s,%s,%s) RETURNING id",
            (email, nome, h, "professor", False, professor_id),
        )
        user_id = cur.fetchone()[0]
        print(f"  Criado usuário: {email}  user_id={user_id}  professor_id={professor_id}")

    # 4. ProfessorInstitution (upsert)
    cur.execute(
        "INSERT INTO professor_institutions (professor_id, institution_id, institutional_email) VALUES (%s,%s,%s) ON CONFLICT DO NOTHING",
        (professor_id, institution_id, email),
    )

    # 5. ResearchGroup — create only if this professor has no group yet
    cur.execute(
        "SELECT pg.group_id FROM professor_groups pg WHERE pg.professor_id = %s LIMIT 1",
        (professor_id,),
    )
    pg_row = cur.fetchone()
    if pg_row:
        group_id = pg_row[0]
        print(f"  Grupo já existe: group_id={group_id}")
    else:
        cur.execute(
            "INSERT INTO research_groups (name, institution_id) VALUES (%s,%s) RETURNING id",
            (f"Grupo de {nome}", institution_id),
        )
        group_id = cur.fetchone()[0]

        # 6. ProfessorGroup
        cur.execute(
            "INSERT INTO professor_groups (professor_id, group_id, role_in_group, institution_id) VALUES (%s,%s,%s,%s) ON CONFLICT DO NOTHING",
            (professor_id, group_id, "coordinator", institution_id),
        )
        print(f"  Criado grupo: group_id={group_id}")

    # 7. Graph layout inicial
    cur.execute("SELECT id FROM graph_layouts WHERE name = 'default'")
    if not cur.fetchone():
        cur.execute(
            "INSERT INTO graph_layouts (name, layout_jsonb) VALUES ('default', %s)",
            (json.dumps({f"p{professor_id}": {"x": 400, "y": 300}}),),
        )


def main():
    url = get_url()
    conn = psycopg2.connect(url)
    conn.autocommit = False
    cur = conn.cursor()

    print("Criando superadmin...")
    upsert_superadmin(cur, SUPERADMIN_EMAIL, SUPERADMIN_NOME, SUPERADMIN_PASSWORD)

    print("Criando professor...")
    upsert_professor(cur, PROFESSOR_EMAIL, PROFESSOR_NOME, PROFESSOR_PASSWORD)

    conn.commit()
    conn.close()
    print("\nSeed concluído.")


if __name__ == "__main__":
    main()

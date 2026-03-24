#!/usr/bin/env python3
"""
Reinicializa o banco: dropa tudo, recria o schema e cria os usuários iniciais.

Uso:
  python seed.py
  python seed.py postgresql://...
"""

import json
import os
import sys
from pathlib import Path

import psycopg2
from passlib.context import CryptContext

pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")

SENHA            = os.getenv("SEED_PASSWORD",      "ghlp1234")
ADMIN_EMAIL      = os.getenv("SEED_ADMIN_EMAIL",   "admin@ufpa.br")
PROFESSOR_EMAIL  = os.getenv("SEED_PROF_EMAIL",    "gpinto@ufpa.br")
PROFESSOR_NOME   = os.getenv("SEED_PROF_NOME",     "Gustavo Pinto")
RESEARCHER_EMAIL = os.getenv("SEED_RES_EMAIL",     "gp@ufpa.br")
RESEARCHER_NOME  = os.getenv("SEED_RES_NOME",      "Gustavo P.")

SCHEMA_FILE = Path(__file__).parent / "migrations" / "000_schema.sql"


def get_url():
    if len(sys.argv) > 1 and not sys.argv[1].startswith("--"):
        return sys.argv[1]
    url = os.getenv("DATABASE_URL", "")
    if not url:
        sys.exit("Erro: DATABASE_URL não definida.")
    return url.replace("postgres://", "postgresql://", 1)


def reset_schema(cur):
    print("Dropando schema público...")
    cur.execute("DROP SCHEMA public CASCADE")
    cur.execute("CREATE SCHEMA public")
    cur.execute("GRANT ALL ON SCHEMA public TO PUBLIC")

    print("Aplicando 000_schema.sql...")
    sql = SCHEMA_FILE.read_text(encoding="utf-8")
    cur.execute(sql)
    print("  Schema recriado.")


def seed_users(cur):
    h = pwd_ctx.hash(SENHA)

    # Institution — derivada do email do professor
    domain    = PROFESSOR_EMAIL.split("@")[-1]
    inst_name = domain.split(".")[0].upper()
    cur.execute(
        "INSERT INTO institutions (name, domain) VALUES (%s,%s) RETURNING id",
        (inst_name, domain),
    )
    institution_id = cur.fetchone()[0]
    print(f"  institution    {inst_name} ({domain})  id={institution_id}")

    # Professor
    cur.execute(
        "INSERT INTO professors (nome, ativo) VALUES (%s, TRUE) RETURNING id",
        (PROFESSOR_NOME,),
    )
    professor_id = cur.fetchone()[0]

    # ProfessorInstitution
    cur.execute(
        "INSERT INTO professor_institutions (professor_id, institution_id, institutional_email) VALUES (%s,%s,%s)",
        (professor_id, institution_id, PROFESSOR_EMAIL),
    )

    # ResearchGroup
    cur.execute(
        "INSERT INTO research_groups (name, institution_id) VALUES (%s,%s) RETURNING id",
        (f"Grupo {inst_name}", institution_id),
    )
    group_id = cur.fetchone()[0]

    # ProfessorGroup
    cur.execute(
        "INSERT INTO professor_groups (professor_id, group_id, role_in_group, institution_id) VALUES (%s,%s,%s,%s)",
        (professor_id, group_id, "coordinator", institution_id),
    )

    # Researcher
    cur.execute(
        """INSERT INTO researchers (nome, status, email, group_id, orientador_id, ativo, registered)
           VALUES (%s,%s,%s,%s,%s,TRUE,TRUE) RETURNING id""",
        (RESEARCHER_NOME, "mestrado", RESEARCHER_EMAIL, group_id, professor_id),
    )
    researcher_id = cur.fetchone()[0]

    # Graph layout inicial
    cur.execute(
        "INSERT INTO graph_layouts (name, layout_jsonb) VALUES ('default', %s)",
        (json.dumps({str(researcher_id): {"x": 400, "y": 300}}),),
    )

    # Users
    users = [
        (ADMIN_EMAIL,      "Admin",          "superadmin", True,  None,         None),
        (PROFESSOR_EMAIL,  PROFESSOR_NOME,   "professor",  False, professor_id, None),
        (RESEARCHER_EMAIL, RESEARCHER_NOME,  "student",    False, None,         researcher_id),
    ]
    for email, nome, role, is_admin, prof_id, res_id in users:
        cur.execute(
            """INSERT INTO users (email, nome, password_hash, role, is_admin, professor_id, researcher_id)
               VALUES (%s,%s,%s,%s,%s,%s,%s)
               ON CONFLICT (email) DO UPDATE
                 SET nome=EXCLUDED.nome, password_hash=EXCLUDED.password_hash,
                     role=EXCLUDED.role, is_admin=EXCLUDED.is_admin,
                     professor_id=EXCLUDED.professor_id, researcher_id=EXCLUDED.researcher_id
               RETURNING id""",
            (email, nome, h, role, is_admin, prof_id, res_id),
        )
        user_id = cur.fetchone()[0]
        print(f"  {role:12s}  {email}  id={user_id}")


def main():
    url = get_url()
    conn = psycopg2.connect(url)
    conn.autocommit = False
    cur = conn.cursor()

    reset_schema(cur)

    print("Criando usuários...")
    seed_users(cur)

    conn.commit()
    conn.close()
    print("\nSeed concluído.")


if __name__ == "__main__":
    main()

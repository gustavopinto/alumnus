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

SENHA = os.getenv("SEED_PASSWORD", "ghlp1234")

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
    domain = "ufpa.br"
    inst_name = "UFPA"

    # Institution
    cur.execute(
        "INSERT INTO institutions (name, domain) VALUES (%s,%s) ON CONFLICT (domain) DO NOTHING RETURNING id",
        (inst_name, domain),
    )
    row = cur.fetchone()
    if not row:
        cur.execute("SELECT id FROM institutions WHERE domain = %s", (domain,))
        row = cur.fetchone()
    institution_id = row[0]

    # Professor
    cur.execute(
        "INSERT INTO professors (nome, ativo) VALUES (%s, TRUE) RETURNING id",
        ("Gustavo Pinto",),
    )
    professor_id = cur.fetchone()[0]

    # ProfessorInstitution
    cur.execute(
        "INSERT INTO professor_institutions (professor_id, institution_id, institutional_email) VALUES (%s,%s,%s)",
        (professor_id, institution_id, "gpinto@ufpa.br"),
    )

    # ResearchGroup
    cur.execute(
        "INSERT INTO research_groups (name, institution_id) VALUES (%s,%s) RETURNING id",
        ("Grupo de Gustavo Pinto", institution_id),
    )
    group_id = cur.fetchone()[0]

    # ProfessorGroup
    cur.execute(
        "INSERT INTO professor_groups (professor_id, group_id, role_in_group, institution_id) VALUES (%s,%s,%s,%s)",
        (professor_id, group_id, "coordinator", institution_id),
    )

    # Researcher (para gp@ufpa.br)
    cur.execute(
        """INSERT INTO researchers (nome, status, email, group_id, orientador_id, ativo, registered)
           VALUES (%s,%s,%s,%s,%s,TRUE,TRUE) RETURNING id""",
        ("Gustavo P.", "mestrado", "gp@ufpa.br", group_id, professor_id),
    )
    researcher_id = cur.fetchone()[0]

    # Graph layout inicial
    cur.execute(
        "INSERT INTO graph_layouts (name, layout_jsonb) VALUES ('default', %s)",
        (json.dumps({str(researcher_id): {"x": 400, "y": 300}}),),
    )

    # Users
    users = [
        ("admin@ufpa.br",  "Admin",         "superadmin", True,  None,          None),
        ("gpinto@ufpa.br", "Gustavo Pinto", "professor",  False, professor_id,  None),
        ("gp@ufpa.br",     "Gustavo P.",    "student",    False, None,          researcher_id),
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

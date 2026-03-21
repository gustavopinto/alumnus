#!/usr/bin/env python3
"""
Cria usuários iniciais no banco (superadmin + professor).

Uso:
  python seed.py
  python seed.py postgresql://...   # URL explícita

Variáveis de ambiente (opcional — senão usa os defaults abaixo):
  SEED_SUPERADMIN_EMAIL
  SEED_SUPERADMIN_PASSWORD
  SEED_SUPERADMIN_NOME
  SEED_PROFESSOR_EMAIL
  SEED_PROFESSOR_PASSWORD
  SEED_PROFESSOR_NOME
"""

import os
import sys

import psycopg2
from passlib.context import CryptContext

pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")

# ── Defaults — altere aqui ou passe via env ──────────────────────────────────
SUPERADMIN_EMAIL    = os.getenv("SEED_SUPERADMIN_EMAIL",    "admin@alumnus.app")
SUPERADMIN_PASSWORD = os.getenv("SEED_SUPERADMIN_PASSWORD", "changeme123")
SUPERADMIN_NOME     = os.getenv("SEED_SUPERADMIN_NOME",     "Superadmin")

PROFESSOR_EMAIL    = os.getenv("SEED_PROFESSOR_EMAIL",    "professor@alumnus.app")
PROFESSOR_PASSWORD = os.getenv("SEED_PROFESSOR_PASSWORD", "changeme123")
PROFESSOR_NOME     = os.getenv("SEED_PROFESSOR_NOME",     "Professor")
# ────────────────────────────────────────────────────────────────────────────


def get_url():
    if len(sys.argv) > 1 and not sys.argv[1].startswith("--"):
        return sys.argv[1]
    url = os.getenv("DATABASE_URL", "")
    if not url:
        sys.exit("Erro: DATABASE_URL não definida.")
    return url.replace("postgres://", "postgresql://", 1)


def upsert_user(cur, email, nome, password, role, is_admin):
    cur.execute("SELECT id FROM users WHERE email = %s", (email,))
    row = cur.fetchone()
    if row:
        print(f"  Já existe: {email} (id={row[0]}) — sem alteração.")
        return
    h = pwd_ctx.hash(password)
    cur.execute(
        """
        INSERT INTO users (email, nome, password_hash, role, is_admin)
        VALUES (%s, %s, %s, %s, %s)
        RETURNING id
        """,
        (email, nome, h, role, is_admin),
    )
    uid = cur.fetchone()[0]
    print(f"  Criado: {email}  role={role}  id={uid}")


def main():
    url = get_url()
    conn = psycopg2.connect(url)
    conn.autocommit = False
    cur = conn.cursor()

    print("Criando superadmin...")
    upsert_user(cur, SUPERADMIN_EMAIL, SUPERADMIN_NOME, SUPERADMIN_PASSWORD,
                role="superadmin", is_admin=True)

    print("Criando professor...")
    upsert_user(cur, PROFESSOR_EMAIL, PROFESSOR_NOME, PROFESSOR_PASSWORD,
                role="professor", is_admin=False)

    conn.commit()
    conn.close()
    print("\nSeed concluído.")


if __name__ == "__main__":
    main()

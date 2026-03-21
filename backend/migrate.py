#!/usr/bin/env python3
"""
Aplica migrations pendentes no banco de dados.

Uso:
  python migrate.py                        # usa DATABASE_URL do ambiente
  python migrate.py postgresql://...       # URL explícita
  python migrate.py --dry-run              # mostra o que seria aplicado
"""

import os
import sys
from pathlib import Path

import psycopg2

MIGRATIONS_DIR = Path(__file__).parent / "migrations"
TRACKING_TABLE = "schema_migrations"


def get_url():
    if len(sys.argv) > 1 and not sys.argv[1].startswith("--"):
        return sys.argv[1]
    url = os.getenv("DATABASE_URL", "")
    if not url:
        sys.exit("Erro: DATABASE_URL não definida. Passe como argumento ou variável de ambiente.")
    # psycopg2 requer postgresql://, não postgres://
    return url.replace("postgres://", "postgresql://", 1)


def ensure_tracking_table(cur):
    cur.execute(f"""
        CREATE TABLE IF NOT EXISTS {TRACKING_TABLE} (
            id      SERIAL PRIMARY KEY,
            name    TEXT UNIQUE NOT NULL,
            applied TIMESTAMPTZ NOT NULL DEFAULT now()
        )
    """)


def applied_migrations(cur):
    cur.execute(f"SELECT name FROM {TRACKING_TABLE} ORDER BY name")
    return {row[0] for row in cur.fetchall()}


def pending_migrations(applied):
    files = sorted(MIGRATIONS_DIR.glob("*.sql"))
    return [f for f in files if f.name not in applied]


def main():
    dry_run = "--dry-run" in sys.argv
    url = get_url()

    conn = psycopg2.connect(url)
    conn.autocommit = False
    cur = conn.cursor()

    ensure_tracking_table(cur)
    conn.commit()

    applied = applied_migrations(cur)
    pending = pending_migrations(applied)

    if not pending:
        print("Nenhuma migration pendente.")
        conn.close()
        return

    for migration in pending:
        print(f"{'[dry-run] ' if dry_run else ''}Aplicando: {migration.name}")
        if not dry_run:
            sql = migration.read_text(encoding="utf-8")
            cur.execute(sql)
            cur.execute(f"INSERT INTO {TRACKING_TABLE} (name) VALUES (%s)", (migration.name,))
            conn.commit()
            print(f"  OK")

    if dry_run:
        print(f"\n{len(pending)} migration(s) seriam aplicadas.")
    else:
        print(f"\n{len(pending)} migration(s) aplicadas com sucesso.")

    conn.close()


if __name__ == "__main__":
    main()

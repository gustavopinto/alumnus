-- Migration 010: milestones e readings passam de researcher_id para user_id
-- Popula user_id a partir do usuário vinculado ao researcher antes de dropar a coluna antiga.
-- Em bancos novos as tabelas já existem com user_id, então os blocos abaixo são no-op.

-- ── milestones ────────────────────────────────────────────────────────────────

DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'milestones' AND column_name = 'researcher_id'
    ) THEN
        ALTER TABLE milestones ADD COLUMN IF NOT EXISTS user_id INTEGER;

        UPDATE milestones m
        SET    user_id = u.id
        FROM   users u
        WHERE  u.researcher_id = m.researcher_id
          AND  m.user_id IS NULL;

        DELETE FROM milestones WHERE user_id IS NULL;

        ALTER TABLE milestones ALTER COLUMN user_id SET NOT NULL;

        ALTER TABLE milestones
            ADD CONSTRAINT milestones_user_id_fkey
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;

        ALTER TABLE milestones DROP COLUMN researcher_id;
    END IF;
END $$;

-- ── readings ──────────────────────────────────────────────────────────────────

DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'readings' AND column_name = 'researcher_id'
    ) THEN
        ALTER TABLE readings ADD COLUMN IF NOT EXISTS user_id INTEGER;

        UPDATE readings r
        SET    user_id = u.id
        FROM   users u
        WHERE  u.researcher_id = r.researcher_id
          AND  r.user_id IS NULL;

        DELETE FROM readings WHERE user_id IS NULL;

        ALTER TABLE readings ALTER COLUMN user_id SET NOT NULL;

        ALTER TABLE readings
            ADD CONSTRAINT readings_user_id_fkey
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;

        ALTER TABLE readings DROP COLUMN researcher_id;
    END IF;
END $$;

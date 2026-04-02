-- Migration 010: milestones e readings passam de researcher_id para user_id
-- Popula user_id a partir do usuário vinculado ao researcher antes de dropar a coluna antiga.

-- ── milestones ────────────────────────────────────────────────────────────────

ALTER TABLE milestones ADD COLUMN IF NOT EXISTS user_id INTEGER;

-- Preenche user_id via researcher → user
UPDATE milestones m
SET    user_id = u.id
FROM   users u
WHERE  u.researcher_id = m.researcher_id
  AND  m.user_id IS NULL;

-- Remove registros órfãos (researcher sem user vinculado) para poder setar NOT NULL
DELETE FROM milestones WHERE user_id IS NULL;

ALTER TABLE milestones ALTER COLUMN user_id SET NOT NULL;

ALTER TABLE milestones
    ADD CONSTRAINT milestones_user_id_fkey
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;

ALTER TABLE milestones DROP COLUMN researcher_id;

-- ── readings ──────────────────────────────────────────────────────────────────

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

-- ============================================================
-- 001_user_researcher_unify.sql
-- User como fonte de verdade: cria User para cada Researcher
-- pendente e remove campos redundantes de researchers.
-- ============================================================

-- 1. password_hash pode ser NULL (usuário convidado mas sem senha ainda)
ALTER TABLE users ALTER COLUMN password_hash DROP NOT NULL;

-- 2. Criar User para cada Researcher pendente que tenha email
INSERT INTO users (email, nome, password_hash, role, is_admin, researcher_id, created_at)
SELECT
    lower(trim(r.email)) AS email,
    r.nome               AS nome,
    NULL                 AS password_hash,
    'student'            AS role,
    FALSE                AS is_admin,
    r.id                 AS researcher_id,
    now()                AS created_at
FROM researchers r
WHERE r.registered = FALSE
  AND r.ativo       = TRUE
  AND r.email IS NOT NULL
  AND trim(r.email) <> ''
  AND NOT EXISTS (
      SELECT 1 FROM users u WHERE lower(u.email) = lower(trim(r.email))
  );

-- 3. Remover colunas redundantes de researchers
ALTER TABLE researchers DROP COLUMN IF EXISTS nome;
ALTER TABLE researchers DROP COLUMN IF EXISTS email;
ALTER TABLE researchers DROP COLUMN IF EXISTS registered;

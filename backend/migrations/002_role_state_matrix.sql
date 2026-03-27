-- Migration 002: Renomeia role 'student' → 'researcher' e reforça consistência de estado
--
-- Mudanças:
--   1. Renomeia role='student' → 'researcher' em todos os registros
--   2. Normaliza is_admin para ser derivado de role (superadmin → true, demais → false)
--   3. Índices UNIQUE parciais em professor_id e researcher_id
--      (PostgreSQL permite múltiplos NULLs — a constraint só se aplica a valores não-nulos)
--   4. CHECK: role deve ser um dos três valores válidos
--   5. CHECK: um usuário não pode ter professor_id E researcher_id simultaneamente

-- 1. Renomeia role
UPDATE users SET role = 'researcher' WHERE role = 'student';

-- 2. Normaliza is_admin
UPDATE users SET is_admin = (role = 'superadmin');

-- 3. Índices UNIQUE parciais
CREATE UNIQUE INDEX IF NOT EXISTS uq_users_professor_id
  ON users(professor_id) WHERE professor_id IS NOT NULL;

CREATE UNIQUE INDEX IF NOT EXISTS uq_users_researcher_id
  ON users(researcher_id) WHERE researcher_id IS NOT NULL;

-- 4. CHECK: role válido
ALTER TABLE users
  ADD CONSTRAINT chk_users_role
  CHECK (role IN ('superadmin', 'professor', 'researcher'));

-- 5. CHECK: não pode ter os dois FKs ao mesmo tempo
ALTER TABLE users
  ADD CONSTRAINT chk_users_no_dual_fk
  CHECK (professor_id IS NULL OR researcher_id IS NULL);

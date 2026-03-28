-- 008: simplify schema
-- Remove colunas redundantes e centraliza estado em users

-- 1. Nome do professor delegado ao User (era duplicado)
ALTER TABLE professors DROP COLUMN IF EXISTS nome;

-- 2. Ativo centralizado em users (remove dos perfis)
ALTER TABLE professors DROP COLUMN IF EXISTS ativo;
ALTER TABLE researchers DROP COLUMN IF EXISTS ativo;

-- 3. is_admin é derivado de role — remove coluna, usa role == 'superadmin'
ALTER TABLE users DROP COLUMN IF EXISTS is_admin;

-- 4. Adiciona ativo em users (padrão TRUE)
ALTER TABLE users ADD COLUMN IF NOT EXISTS ativo BOOLEAN NOT NULL DEFAULT TRUE;

-- 5. Garante constraint: usuário não pode ser professor E pesquisador ao mesmo tempo
ALTER TABLE users DROP CONSTRAINT IF EXISTS chk_users_no_dual_fk;
ALTER TABLE users ADD CONSTRAINT chk_users_no_dual_fk
    CHECK (professor_id IS NULL OR researcher_id IS NULL);

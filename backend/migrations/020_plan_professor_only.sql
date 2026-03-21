-- Plano (trial/mensal/anual) apenas para usuários com role = professor.
-- Primeiro remove NOT NULL para permitir NULL em alunos/admin; depois limpa linhas.
ALTER TABLE users ALTER COLUMN plan_type DROP DEFAULT;
ALTER TABLE users ALTER COLUMN plan_type DROP NOT NULL;

ALTER TABLE users ALTER COLUMN plan_status DROP DEFAULT;
ALTER TABLE users ALTER COLUMN plan_status DROP NOT NULL;

ALTER TABLE users ALTER COLUMN account_activated_at DROP DEFAULT;
ALTER TABLE users ALTER COLUMN account_activated_at DROP NOT NULL;

UPDATE users
SET plan_type = NULL,
    plan_status = NULL,
    account_activated_at = NULL,
    plan_period_ends_at = NULL
WHERE role IS DISTINCT FROM 'professor';

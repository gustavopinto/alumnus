-- Assinatura/plano só pode existir para role = professor (admin e alunos sem registro).
UPDATE users
SET plan_type = NULL,
    plan_status = NULL,
    account_activated_at = NULL,
    plan_period_ends_at = NULL
WHERE role IS DISTINCT FROM 'professor';

ALTER TABLE users ADD CONSTRAINT users_subscription_only_professor CHECK (
  (role = 'professor') OR (
    plan_type IS NULL
    AND plan_status IS NULL
    AND account_activated_at IS NULL
    AND plan_period_ends_at IS NULL
  )
);

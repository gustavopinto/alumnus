-- Assinatura: professor e superadmin podem ter plano; aluno e admin (painel) nunca.
ALTER TABLE users DROP CONSTRAINT IF EXISTS users_subscription_only_professor;

ALTER TABLE users ADD CONSTRAINT users_subscription_only_professor CHECK (
  (role IN ('student', 'admin') AND plan_type IS NULL AND plan_status IS NULL AND account_activated_at IS NULL AND plan_period_ends_at IS NULL)
  OR
  (role NOT IN ('student', 'admin'))
);

-- Plano: trial (30 dias), mensal ou anual; status ativo ou vencido.
ALTER TABLE users ADD COLUMN IF NOT EXISTS plan_type VARCHAR(20) NOT NULL DEFAULT 'trial';
ALTER TABLE users ADD COLUMN IF NOT EXISTS plan_status VARCHAR(20) NOT NULL DEFAULT 'active';
ALTER TABLE users ADD COLUMN IF NOT EXISTS account_activated_at TIMESTAMPTZ;
UPDATE users SET account_activated_at = created_at WHERE account_activated_at IS NULL;
ALTER TABLE users ALTER COLUMN account_activated_at SET NOT NULL;
ALTER TABLE users ALTER COLUMN account_activated_at SET DEFAULT now();

ALTER TABLE users ADD COLUMN IF NOT EXISTS plan_period_ends_at TIMESTAMPTZ;
UPDATE users
SET plan_period_ends_at = account_activated_at + INTERVAL '30 days'
WHERE plan_type = 'trial' AND plan_period_ends_at IS NULL;

UPDATE users
SET plan_status = 'expired'
WHERE plan_period_ends_at IS NOT NULL AND plan_period_ends_at <= now();

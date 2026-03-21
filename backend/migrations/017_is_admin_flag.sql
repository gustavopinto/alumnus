-- Adiciona flag is_admin separada do role, permitindo que professores também sejam admin
ALTER TABLE users ADD COLUMN IF NOT EXISTS is_admin BOOLEAN NOT NULL DEFAULT FALSE;

-- Marca os usuários com role='admin' como is_admin=true
UPDATE users SET is_admin = TRUE WHERE role = 'admin';

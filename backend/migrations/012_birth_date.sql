-- Migration 012: adiciona data de nascimento aos usuários.
-- Usuários existentes recebem 1990-01-01 como placeholder.

ALTER TABLE users ADD COLUMN IF NOT EXISTS birth_date DATE;

UPDATE users SET birth_date = '1990-01-01' WHERE birth_date IS NULL;

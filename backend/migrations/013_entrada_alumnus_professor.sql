-- Migration 013: cria marco "Entrada no Alumnus" para professores existentes.
-- Idempotente: ignora usuários que já têm um marco do tipo "entrada".

INSERT INTO milestones (user_id, type, title, date, created_by_id, created_at)
SELECT
    u.id,
    'entrada',
    'Entrada no Alumnus',
    u.created_at::date,
    u.id,
    now()
FROM users u
WHERE u.role = 'professor'
  AND NOT EXISTS (
      SELECT 1 FROM milestones m
      WHERE m.user_id = u.id AND m.type = 'entrada'
  );

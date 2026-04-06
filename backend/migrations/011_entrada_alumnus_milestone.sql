-- Migration 011: cria marco "Entrada no Alumnus" para todos os pesquisadores existentes.
-- Usa users.created_at como data de ingresso no sistema.
-- Idempotente: ignora usuários que já têm um marco do tipo "entrada".

INSERT INTO milestones (user_id, type, title, date, created_by_id, created_at)
SELECT
    u.id,
    'entrada',
    'Entrada no Alumnus',
    COALESCE(u.created_at, now())::date,
    u.id,
    now()
FROM users u
WHERE u.role = 'researcher'
  AND NOT EXISTS (
      SELECT 1 FROM milestones m
      WHERE m.user_id = u.id AND m.type = 'entrada'
  );

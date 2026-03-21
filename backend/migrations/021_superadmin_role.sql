-- 021: Introduz role superadmin e reorganiza hierarquia de papéis
--
-- Hierarquia nova:
--   student    → acesso somente ao próprio perfil
--   professor  → acessa o dashboard filtrado ao próprio grupo
--   admin      → acessa o dashboard filtrado ao próprio grupo (sem perfil de pesquisador)
--   superadmin → acesso total a todos os grupos
--
-- Migração: antigos admin (role='admin') tornam-se superadmin.
-- is_admin passa a ser derivado do role (True apenas para admin/superadmin).

UPDATE users
SET role = 'superadmin'
WHERE role = 'admin';

-- Atualiza flag is_admin para consistência com os novos papéis
UPDATE users SET is_admin = TRUE  WHERE role IN ('admin', 'superadmin');
UPDATE users SET is_admin = FALSE WHERE role NOT IN ('admin', 'superadmin');

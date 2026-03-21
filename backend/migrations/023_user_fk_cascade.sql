-- Ao remover um usuário: SET NULL nas FKs de conteúdo (notas, lembretes, manual, board)
-- para preservar o conteúdo sem o autor; CASCADE nas FKs de participação (leituras, votos, interesses).

ALTER TABLE notes
  DROP CONSTRAINT IF EXISTS notes_created_by_id_fkey,
  ADD CONSTRAINT notes_created_by_id_fkey
    FOREIGN KEY (created_by_id) REFERENCES users(id) ON DELETE SET NULL;

ALTER TABLE reminders
  DROP CONSTRAINT IF EXISTS reminders_created_by_id_fkey,
  ADD CONSTRAINT reminders_created_by_id_fkey
    FOREIGN KEY (created_by_id) REFERENCES users(id) ON DELETE SET NULL;

ALTER TABLE board_posts
  DROP CONSTRAINT IF EXISTS board_posts_author_id_fkey,
  ADD CONSTRAINT board_posts_author_id_fkey
    FOREIGN KEY (author_id) REFERENCES users(id) ON DELETE SET NULL;

ALTER TABLE manual_entries
  DROP CONSTRAINT IF EXISTS manual_entries_author_id_fkey,
  ADD CONSTRAINT manual_entries_author_id_fkey
    FOREIGN KEY (author_id) REFERENCES users(id) ON DELETE SET NULL;

ALTER TABLE manual_comments
  DROP CONSTRAINT IF EXISTS manual_comments_author_id_fkey,
  ADD CONSTRAINT manual_comments_author_id_fkey
    FOREIGN KEY (author_id) REFERENCES users(id) ON DELETE SET NULL;

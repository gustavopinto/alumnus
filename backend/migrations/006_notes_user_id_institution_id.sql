-- Add user_id and institution_id to notes table (for professor profile notes)
-- and make researcher_id nullable (notes can target either a researcher or a user)

ALTER TABLE notes ADD COLUMN IF NOT EXISTS user_id INTEGER REFERENCES users(id) ON DELETE SET NULL;
ALTER TABLE notes ADD COLUMN IF NOT EXISTS institution_id INTEGER REFERENCES institutions(id) ON DELETE SET NULL;
ALTER TABLE notes ALTER COLUMN researcher_id DROP NOT NULL;

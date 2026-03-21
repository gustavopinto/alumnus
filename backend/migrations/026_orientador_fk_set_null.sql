-- Fix orientador_id FK so deleting a researcher who is someone's orientador
-- sets orientador_id to NULL instead of raising a ForeignKeyViolation.
ALTER TABLE researchers
    DROP CONSTRAINT IF EXISTS researchers_orientador_id_fkey;

ALTER TABLE researchers
    ADD CONSTRAINT researchers_orientador_id_fkey
    FOREIGN KEY (orientador_id) REFERENCES researchers(id)
    ON DELETE SET NULL;

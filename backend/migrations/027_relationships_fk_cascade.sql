-- Fix CASCADE on relationships FKs — migration 024 used wrong constraint names.
-- Drop both old-named and new-named variants to be safe, then recreate with CASCADE.

ALTER TABLE relationships
    DROP CONSTRAINT IF EXISTS relationships_source_student_id_fkey,
    DROP CONSTRAINT IF EXISTS relationships_source_researcher_id_fkey;

ALTER TABLE relationships
    ADD CONSTRAINT relationships_source_researcher_id_fkey
    FOREIGN KEY (source_researcher_id) REFERENCES researchers(id) ON DELETE CASCADE;

ALTER TABLE relationships
    DROP CONSTRAINT IF EXISTS relationships_target_student_id_fkey,
    DROP CONSTRAINT IF EXISTS relationships_target_researcher_id_fkey;

ALTER TABLE relationships
    ADD CONSTRAINT relationships_target_researcher_id_fkey
    FOREIGN KEY (target_researcher_id) REFERENCES researchers(id) ON DELETE CASCADE;

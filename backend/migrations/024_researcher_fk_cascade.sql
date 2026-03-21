-- Ao remover um pesquisador: CASCADE nas relações (grafo) e SET NULL nas demais referências.

ALTER TABLE relationships
  DROP CONSTRAINT IF EXISTS relationships_source_student_id_fkey,
  ADD CONSTRAINT relationships_source_student_id_fkey
    FOREIGN KEY (source_researcher_id) REFERENCES researchers(id) ON DELETE CASCADE;

ALTER TABLE relationships
  DROP CONSTRAINT IF EXISTS relationships_target_student_id_fkey,
  ADD CONSTRAINT relationships_target_student_id_fkey
    FOREIGN KEY (target_researcher_id) REFERENCES researchers(id) ON DELETE CASCADE;

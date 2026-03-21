ALTER TABLE students RENAME TO researchers;

ALTER TABLE relationships RENAME COLUMN source_student_id TO source_researcher_id;
ALTER TABLE relationships RENAME COLUMN target_student_id TO target_researcher_id;

ALTER TABLE notes RENAME COLUMN student_id TO researcher_id;
ALTER TABLE works RENAME COLUMN student_id TO researcher_id;
ALTER TABLE users RENAME COLUMN student_id TO researcher_id;

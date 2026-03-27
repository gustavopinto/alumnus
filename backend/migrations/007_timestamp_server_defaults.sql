-- Adiciona DEFAULT now() nas colunas created_at/updated_at que ficaram sem
-- server default quando criadas pelo SQLAlchemy create_all() (que só aplica
-- defaults no lado Python, não no banco).

ALTER TABLE institutions           ALTER COLUMN created_at SET DEFAULT now();
ALTER TABLE professors             ALTER COLUMN created_at SET DEFAULT now();
ALTER TABLE professors             ALTER COLUMN updated_at SET DEFAULT now();
ALTER TABLE professor_institutions ALTER COLUMN created_at SET DEFAULT now();
ALTER TABLE research_groups        ALTER COLUMN created_at SET DEFAULT now();
ALTER TABLE professor_groups       ALTER COLUMN created_at SET DEFAULT now();
ALTER TABLE researchers            ALTER COLUMN created_at SET DEFAULT now();
ALTER TABLE researchers            ALTER COLUMN updated_at SET DEFAULT now();
ALTER TABLE relationships          ALTER COLUMN created_at SET DEFAULT now();
ALTER TABLE notes                  ALTER COLUMN created_at SET DEFAULT now();
ALTER TABLE users                  ALTER COLUMN created_at SET DEFAULT now();
ALTER TABLE file_uploads           ALTER COLUMN created_at SET DEFAULT now();
ALTER TABLE graph_layouts          ALTER COLUMN updated_at SET DEFAULT now();
ALTER TABLE reminders              ALTER COLUMN created_at SET DEFAULT now();
ALTER TABLE tips                   ALTER COLUMN created_at SET DEFAULT now();
ALTER TABLE tip_comments           ALTER COLUMN created_at SET DEFAULT now();
ALTER TABLE deadlines              ALTER COLUMN created_at SET DEFAULT now();
ALTER TABLE deadline_interests     ALTER COLUMN created_at SET DEFAULT now();

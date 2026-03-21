CREATE TABLE IF NOT EXISTS reminders (
    id          SERIAL PRIMARY KEY,
    text        TEXT NOT NULL,
    due_date    DATE,
    done        BOOLEAN NOT NULL DEFAULT FALSE,
    created_by_id INTEGER REFERENCES users(id),
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

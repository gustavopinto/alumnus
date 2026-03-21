CREATE TABLE IF NOT EXISTS manual_entries (
    id         SERIAL PRIMARY KEY,
    question   TEXT NOT NULL,
    answer     TEXT NOT NULL,
    author_id  INTEGER REFERENCES users(id),
    position   INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS manual_votes (
    entry_id INTEGER NOT NULL REFERENCES manual_entries(id) ON DELETE CASCADE,
    user_id  INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    PRIMARY KEY (entry_id, user_id)
);

CREATE TABLE IF NOT EXISTS manual_comments (
    id         SERIAL PRIMARY KEY,
    entry_id   INTEGER NOT NULL REFERENCES manual_entries(id) ON DELETE CASCADE,
    text       TEXT NOT NULL,
    author_id  INTEGER REFERENCES users(id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

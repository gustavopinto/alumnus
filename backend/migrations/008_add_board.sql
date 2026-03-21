CREATE TABLE IF NOT EXISTS board_posts (
    id          SERIAL PRIMARY KEY,
    text        TEXT NOT NULL,
    author_id   INTEGER REFERENCES users(id),
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

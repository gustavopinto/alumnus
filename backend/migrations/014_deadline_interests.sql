CREATE TABLE IF NOT EXISTS deadline_interests (
    id          SERIAL PRIMARY KEY,
    deadline_key VARCHAR(200) NOT NULL,
    user_id     INTEGER REFERENCES users(id) ON DELETE CASCADE,
    created_at  TIMESTAMP DEFAULT now(),
    UNIQUE (deadline_key, user_id)
);

-- Schema consolidado — substitui todas as migrations incrementais anteriores.
-- Todos os FKs já incluem ON DELETE correto.

CREATE TABLE IF NOT EXISTS researchers (
    id               SERIAL PRIMARY KEY,
    nome             VARCHAR(255) NOT NULL,
    photo_url        VARCHAR(500),
    photo_thumb_url  VARCHAR(500),
    status           VARCHAR(50)  NOT NULL,
    email            VARCHAR(255),
    orientador_id    INTEGER REFERENCES researchers(id) ON DELETE SET NULL,
    observacoes      TEXT,
    ativo            BOOLEAN NOT NULL DEFAULT TRUE,
    registered       BOOLEAN NOT NULL DEFAULT FALSE,
    lattes_url       VARCHAR(500),
    scholar_url      VARCHAR(500),
    linkedin_url     VARCHAR(500),
    github_url       VARCHAR(500),
    instagram_url    VARCHAR(50),
    twitter_url      VARCHAR(50),
    whatsapp         VARCHAR(20),
    interesses       TEXT,
    matricula        VARCHAR(50),
    curso            VARCHAR(255),
    enrollment_date  DATE,
    created_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at       TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS relationships (
    id                   SERIAL PRIMARY KEY,
    source_researcher_id INTEGER NOT NULL REFERENCES researchers(id) ON DELETE CASCADE,
    target_researcher_id INTEGER NOT NULL REFERENCES researchers(id) ON DELETE CASCADE,
    relation_type        VARCHAR(50) NOT NULL,
    created_at           TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS users (
    id                   SERIAL PRIMARY KEY,
    email                VARCHAR(255) UNIQUE NOT NULL,
    nome                 VARCHAR(255) NOT NULL,
    password_hash        VARCHAR(255) NOT NULL,
    role                 VARCHAR(20)  NOT NULL,
    is_admin             BOOLEAN NOT NULL DEFAULT FALSE,
    researcher_id        INTEGER REFERENCES researchers(id) ON DELETE SET NULL,
    last_login           TIMESTAMPTZ,
    plan_type            VARCHAR(20),
    plan_status          VARCHAR(20),
    account_activated_at TIMESTAMPTZ,
    plan_period_ends_at  TIMESTAMPTZ,
    created_at           TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS works (
    id            SERIAL PRIMARY KEY,
    researcher_id INTEGER NOT NULL REFERENCES researchers(id) ON DELETE CASCADE,
    title         VARCHAR(500) NOT NULL,
    type          VARCHAR(50)  NOT NULL,
    description   TEXT,
    year          INTEGER,
    url           VARCHAR(500),
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS notes (
    id            SERIAL PRIMARY KEY,
    researcher_id INTEGER NOT NULL REFERENCES researchers(id) ON DELETE CASCADE,
    text          TEXT NOT NULL,
    file_url      VARCHAR(500),
    file_name     VARCHAR(255),
    created_by_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS file_uploads (
    id            SERIAL PRIMARY KEY,
    data          BYTEA        NOT NULL,
    mime_type     VARCHAR(100) NOT NULL,
    original_name VARCHAR(255) NOT NULL,
    created_at    TIMESTAMPTZ  NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS graph_layouts (
    id           SERIAL PRIMARY KEY,
    name         VARCHAR(100) DEFAULT 'default',
    layout_jsonb JSONB        DEFAULT '{}',
    updated_at   TIMESTAMPTZ  NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS reminders (
    id            SERIAL PRIMARY KEY,
    text          TEXT NOT NULL,
    due_date      DATE,
    done          BOOLEAN NOT NULL DEFAULT FALSE,
    created_by_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS board_posts (
    id         SERIAL PRIMARY KEY,
    text       TEXT NOT NULL,
    author_id  INTEGER REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS manual_entries (
    id         SERIAL PRIMARY KEY,
    question   TEXT NOT NULL,
    answer     TEXT NOT NULL,
    author_id  INTEGER REFERENCES users(id) ON DELETE SET NULL,
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
    author_id  INTEGER REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS deadline_interests (
    id           SERIAL PRIMARY KEY,
    deadline_key VARCHAR(200) NOT NULL,
    user_id      INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (deadline_key, user_id)
);

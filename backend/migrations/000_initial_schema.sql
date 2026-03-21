-- Schema inicial (estado do banco antes das migrations incrementais)
CREATE TABLE IF NOT EXISTS students (
    id            SERIAL PRIMARY KEY,
    nome          VARCHAR(255) NOT NULL,
    photo_url     VARCHAR(500),
    status        VARCHAR(50)  NOT NULL,
    email         VARCHAR(255),
    orientador_id INTEGER REFERENCES students(id),
    observacoes   TEXT,
    ativo         BOOLEAN NOT NULL DEFAULT TRUE,
    registered    BOOLEAN NOT NULL DEFAULT FALSE,
    lattes_url    VARCHAR(500),
    scholar_url   VARCHAR(500),
    linkedin_url  VARCHAR(500),
    github_url    VARCHAR(500),
    interesses    TEXT,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS relationships (
    id                  SERIAL PRIMARY KEY,
    source_student_id   INTEGER NOT NULL REFERENCES students(id),
    target_student_id   INTEGER NOT NULL REFERENCES students(id),
    relation_type       VARCHAR(50) NOT NULL,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS users (
    id            SERIAL PRIMARY KEY,
    email         VARCHAR(255) UNIQUE NOT NULL,
    nome          VARCHAR(255) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role          VARCHAR(20)  NOT NULL,
    student_id    INTEGER REFERENCES students(id),
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS works (
    id          SERIAL PRIMARY KEY,
    student_id  INTEGER NOT NULL REFERENCES students(id),
    title       VARCHAR(500) NOT NULL,
    type        VARCHAR(50)  NOT NULL,
    description TEXT,
    year        INTEGER,
    url         VARCHAR(500),
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS notes (
    id          SERIAL PRIMARY KEY,
    student_id  INTEGER NOT NULL REFERENCES students(id),
    text        TEXT NOT NULL,
    file_url    VARCHAR(500),
    file_name   VARCHAR(255),
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS file_uploads (
    id            SERIAL PRIMARY KEY,
    data          BYTEA        NOT NULL,
    mime_type     VARCHAR(100) NOT NULL,
    original_name VARCHAR(255) NOT NULL,
    created_at    TIMESTAMPTZ  NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS graph_layouts (
    id          SERIAL PRIMARY KEY,
    name        VARCHAR(100) DEFAULT 'default',
    layout_jsonb JSONB DEFAULT '{}',
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

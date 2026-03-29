-- 009: troca photo_url/photo_thumb_url (text) por FKs inteiras para file_uploads

-- 1. Adiciona colunas FK
ALTER TABLE users
    ADD COLUMN IF NOT EXISTS photo_file_id       INTEGER REFERENCES file_uploads(id),
    ADD COLUMN IF NOT EXISTS photo_thumb_file_id INTEGER REFERENCES file_uploads(id);

-- 2. Migra dados existentes extraindo o id do padrão /api/files/{id}
UPDATE users
SET
    photo_file_id = CAST(
        NULLIF(REGEXP_REPLACE(photo_url, '^/api/files/(\d+)$', '\1'), photo_url)
        AS INTEGER
    ),
    photo_thumb_file_id = CAST(
        NULLIF(REGEXP_REPLACE(photo_thumb_url, '^/api/files/(\d+)$', '\1'), photo_thumb_url)
        AS INTEGER
    )
WHERE photo_url IS NOT NULL OR photo_thumb_url IS NOT NULL;

-- 3. Remove colunas antigas
ALTER TABLE users
    DROP COLUMN IF EXISTS photo_url,
    DROP COLUMN IF EXISTS photo_thumb_url;

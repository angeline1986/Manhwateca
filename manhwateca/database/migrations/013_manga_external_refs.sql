CREATE TABLE IF NOT EXISTS manhwateca.manga_external_refs (
    id BIGSERIAL PRIMARY KEY,
    manga_id BIGINT NOT NULL REFERENCES manhwateca.mangas(id) ON DELETE CASCADE,
    provider TEXT NOT NULL CHECK (btrim(provider) <> ''),
    external_id TEXT NOT NULL CHECK (btrim(external_id) <> ''),
    external_url TEXT,
    external_title TEXT,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (manga_id, provider),
    UNIQUE (provider, external_id)
);

CREATE OR REPLACE FUNCTION manhwateca.touch_manga_external_refs_updated_at()
RETURNS trigger AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_manga_external_refs_updated_at
ON manhwateca.manga_external_refs;
CREATE TRIGGER trg_manga_external_refs_updated_at
BEFORE UPDATE ON manhwateca.manga_external_refs
FOR EACH ROW
EXECUTE FUNCTION manhwateca.touch_manga_external_refs_updated_at();

CREATE INDEX IF NOT EXISTS idx_manga_external_refs_manga_id
ON manhwateca.manga_external_refs(manga_id);

CREATE INDEX IF NOT EXISTS idx_manga_external_refs_provider
ON manhwateca.manga_external_refs(provider);

INSERT INTO manhwateca.manga_external_refs(
    manga_id,
    provider,
    external_id,
    external_url,
    external_title,
    metadata
)
SELECT
    m.id,
    'mangaupdates',
    btrim(m.work_code),
    NULLIF(btrim(m.mangaupdates_url), ''),
    NULLIF(btrim(m.title), ''),
    '{}'::jsonb
FROM manhwateca.mangas m
WHERE m.work_code IS NOT NULL
  AND btrim(m.work_code) <> ''
ON CONFLICT DO NOTHING;

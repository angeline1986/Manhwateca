CREATE TABLE IF NOT EXISTS manhwateca.external_releases (
    id BIGSERIAL PRIMARY KEY,
    manga_id BIGINT REFERENCES manhwateca.mangas(id) ON DELETE SET NULL,
    provider TEXT NOT NULL CHECK (btrim(provider) <> ''),
    external_series_id TEXT NOT NULL CHECK (btrim(external_series_id) <> ''),
    external_release_id TEXT,
    volume TEXT,
    chapter TEXT,
    normalized_volume TEXT NOT NULL DEFAULT '',
    normalized_chapter TEXT NOT NULL DEFAULT '',
    release_date DATE NOT NULL,
    language TEXT,
    title TEXT,
    source_url TEXT,
    raw_payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    first_seen_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    last_seen_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    viewed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE OR REPLACE FUNCTION manhwateca.touch_external_releases_updated_at()
RETURNS trigger AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_external_releases_updated_at
ON manhwateca.external_releases;
CREATE TRIGGER trg_external_releases_updated_at
BEFORE UPDATE ON manhwateca.external_releases
FOR EACH ROW
EXECUTE FUNCTION manhwateca.touch_external_releases_updated_at();

CREATE UNIQUE INDEX IF NOT EXISTS uq_external_releases_external_id
ON manhwateca.external_releases(provider, external_release_id)
WHERE external_release_id IS NOT NULL AND btrim(external_release_id) <> '';

CREATE UNIQUE INDEX IF NOT EXISTS uq_external_releases_fallback
ON manhwateca.external_releases(
    provider,
    external_series_id,
    release_date,
    normalized_chapter,
    normalized_volume
)
WHERE external_release_id IS NULL OR btrim(external_release_id) = '';

CREATE INDEX IF NOT EXISTS idx_external_releases_manga_id
ON manhwateca.external_releases(manga_id);

CREATE INDEX IF NOT EXISTS idx_external_releases_provider
ON manhwateca.external_releases(provider);

CREATE INDEX IF NOT EXISTS idx_external_releases_series
ON manhwateca.external_releases(provider, external_series_id);

CREATE INDEX IF NOT EXISTS idx_external_releases_release_date
ON manhwateca.external_releases(release_date DESC);

CREATE INDEX IF NOT EXISTS idx_external_releases_first_seen
ON manhwateca.external_releases(first_seen_at DESC);

CREATE INDEX IF NOT EXISTS idx_external_releases_viewed
ON manhwateca.external_releases(viewed_at);

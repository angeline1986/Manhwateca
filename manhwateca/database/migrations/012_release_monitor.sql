CREATE TABLE IF NOT EXISTS manhwateca.release_monitor_subscriptions (
    id BIGSERIAL PRIMARY KEY,
    manga_id BIGINT NOT NULL REFERENCES manhwateca.mangas(id) ON DELETE CASCADE,
    enabled BOOLEAN NOT NULL DEFAULT FALSE,
    monitor_mode VARCHAR(30) NOT NULL DEFAULT 'releases',
    last_checked_at TIMESTAMPTZ,
    last_success_at TIMESTAMPTZ,
    last_error_at TIMESTAMPTZ,
    last_error_message TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (manga_id)
);

CREATE TABLE IF NOT EXISTS manhwateca.mangaupdates_releases (
    id BIGSERIAL PRIMARY KEY,
    manga_id BIGINT REFERENCES manhwateca.mangas(id) ON DELETE SET NULL,
    mangaupdates_series_id BIGINT NOT NULL,
    external_release_id TEXT,
    volume TEXT,
    chapter TEXT NOT NULL,
    normalized_volume TEXT NOT NULL DEFAULT '',
    normalized_chapter TEXT NOT NULL,
    release_date DATE NOT NULL,
    release_group TEXT,
    normalized_release_group TEXT NOT NULL DEFAULT '',
    source_url TEXT,
    source_payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    first_seen_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    last_seen_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    viewed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS manhwateca.release_monitor_runs (
    id BIGSERIAL PRIMARY KEY,
    reference_date DATE NOT NULL,
    timezone TEXT NOT NULL,
    status VARCHAR(30) NOT NULL CHECK (
        status IN ('running', 'success', 'partial_success', 'failed')
    ),
    started_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    finished_at TIMESTAMPTZ,
    pages_requested INTEGER NOT NULL DEFAULT 0,
    releases_received INTEGER NOT NULL DEFAULT 0,
    releases_in_period INTEGER NOT NULL DEFAULT 0,
    releases_matched INTEGER NOT NULL DEFAULT 0,
    releases_inserted INTEGER NOT NULL DEFAULT 0,
    releases_already_known INTEGER NOT NULL DEFAULT 0,
    releases_unmatched INTEGER NOT NULL DEFAULT 0,
    error_message TEXT
);

CREATE OR REPLACE FUNCTION manhwateca.touch_release_monitor_updated_at()
RETURNS trigger AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_release_monitor_subscriptions_updated_at
ON manhwateca.release_monitor_subscriptions;
CREATE TRIGGER trg_release_monitor_subscriptions_updated_at
BEFORE UPDATE ON manhwateca.release_monitor_subscriptions
FOR EACH ROW
EXECUTE FUNCTION manhwateca.touch_release_monitor_updated_at();

DROP TRIGGER IF EXISTS trg_mangaupdates_releases_updated_at
ON manhwateca.mangaupdates_releases;
CREATE TRIGGER trg_mangaupdates_releases_updated_at
BEFORE UPDATE ON manhwateca.mangaupdates_releases
FOR EACH ROW
EXECUTE FUNCTION manhwateca.touch_release_monitor_updated_at();

CREATE UNIQUE INDEX IF NOT EXISTS uq_mu_releases_external_id
ON manhwateca.mangaupdates_releases(mangaupdates_series_id, external_release_id)
WHERE external_release_id IS NOT NULL AND btrim(external_release_id) <> '';

CREATE UNIQUE INDEX IF NOT EXISTS uq_mu_releases_fallback
ON manhwateca.mangaupdates_releases(
    mangaupdates_series_id,
    release_date,
    normalized_chapter,
    normalized_release_group,
    normalized_volume
)
WHERE external_release_id IS NULL OR btrim(external_release_id) = '';

CREATE INDEX IF NOT EXISTS idx_mu_releases_release_date
ON manhwateca.mangaupdates_releases(release_date DESC);

CREATE INDEX IF NOT EXISTS idx_mu_releases_manga_id
ON manhwateca.mangaupdates_releases(manga_id);

CREATE INDEX IF NOT EXISTS idx_mu_releases_series_id
ON manhwateca.mangaupdates_releases(mangaupdates_series_id);

CREATE INDEX IF NOT EXISTS idx_mu_releases_first_seen
ON manhwateca.mangaupdates_releases(first_seen_at DESC);

CREATE INDEX IF NOT EXISTS idx_mu_releases_viewed
ON manhwateca.mangaupdates_releases(viewed_at);

CREATE INDEX IF NOT EXISTS idx_release_subscriptions_enabled
ON manhwateca.release_monitor_subscriptions(enabled)
WHERE enabled = TRUE;

CREATE INDEX IF NOT EXISTS idx_release_monitor_runs_started
ON manhwateca.release_monitor_runs(started_at DESC);

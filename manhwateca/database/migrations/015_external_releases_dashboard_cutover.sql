ALTER TABLE manhwateca.external_releases
ADD COLUMN IF NOT EXISTS release_group TEXT;

ALTER TABLE manhwateca.external_releases
ADD COLUMN IF NOT EXISTS normalized_release_group TEXT NOT NULL DEFAULT '';

DROP INDEX IF EXISTS manhwateca.uq_external_releases_fallback;

CREATE UNIQUE INDEX IF NOT EXISTS uq_external_releases_fallback
ON manhwateca.external_releases(
    provider,
    external_series_id,
    release_date,
    normalized_chapter,
    normalized_release_group,
    normalized_volume
)
WHERE external_release_id IS NULL OR btrim(external_release_id) = '';

INSERT INTO manhwateca.external_releases(
    manga_id,
    provider,
    external_series_id,
    external_release_id,
    volume,
    chapter,
    normalized_volume,
    normalized_chapter,
    release_date,
    release_group,
    normalized_release_group,
    source_url,
    raw_payload,
    first_seen_at,
    last_seen_at,
    viewed_at,
    created_at,
    updated_at
)
SELECT
    manga_id,
    'mangaupdates',
    mangaupdates_series_id::text,
    external_release_id,
    volume,
    chapter,
    normalized_volume,
    normalized_chapter,
    release_date,
    release_group,
    normalized_release_group,
    source_url,
    source_payload,
    first_seen_at,
    last_seen_at,
    viewed_at,
    created_at,
    updated_at
FROM manhwateca.mangaupdates_releases
WHERE external_release_id IS NOT NULL
  AND btrim(external_release_id) <> ''
ON CONFLICT (provider, external_release_id)
WHERE external_release_id IS NOT NULL AND btrim(external_release_id) <> ''
DO UPDATE SET manga_id = COALESCE(manhwateca.external_releases.manga_id, EXCLUDED.manga_id),
              external_series_id = EXCLUDED.external_series_id,
              volume = EXCLUDED.volume,
              chapter = EXCLUDED.chapter,
              normalized_volume = EXCLUDED.normalized_volume,
              normalized_chapter = EXCLUDED.normalized_chapter,
              release_date = EXCLUDED.release_date,
              release_group = EXCLUDED.release_group,
              normalized_release_group = EXCLUDED.normalized_release_group,
              source_url = EXCLUDED.source_url,
              raw_payload = EXCLUDED.raw_payload,
              first_seen_at = LEAST(manhwateca.external_releases.first_seen_at, EXCLUDED.first_seen_at),
              last_seen_at = GREATEST(manhwateca.external_releases.last_seen_at, EXCLUDED.last_seen_at),
              viewed_at = COALESCE(manhwateca.external_releases.viewed_at, EXCLUDED.viewed_at);

INSERT INTO manhwateca.external_releases(
    manga_id,
    provider,
    external_series_id,
    external_release_id,
    volume,
    chapter,
    normalized_volume,
    normalized_chapter,
    release_date,
    release_group,
    normalized_release_group,
    source_url,
    raw_payload,
    first_seen_at,
    last_seen_at,
    viewed_at,
    created_at,
    updated_at
)
SELECT
    manga_id,
    'mangaupdates',
    mangaupdates_series_id::text,
    NULL,
    volume,
    chapter,
    normalized_volume,
    normalized_chapter,
    release_date,
    release_group,
    normalized_release_group,
    source_url,
    source_payload,
    first_seen_at,
    last_seen_at,
    viewed_at,
    created_at,
    updated_at
FROM manhwateca.mangaupdates_releases
WHERE external_release_id IS NULL
   OR btrim(external_release_id) = ''
ON CONFLICT (
    provider,
    external_series_id,
    release_date,
    normalized_chapter,
    normalized_release_group,
    normalized_volume
)
WHERE external_release_id IS NULL OR btrim(external_release_id) = ''
DO UPDATE SET manga_id = COALESCE(manhwateca.external_releases.manga_id, EXCLUDED.manga_id),
              volume = EXCLUDED.volume,
              chapter = EXCLUDED.chapter,
              release_group = EXCLUDED.release_group,
              normalized_release_group = EXCLUDED.normalized_release_group,
              source_url = EXCLUDED.source_url,
              raw_payload = EXCLUDED.raw_payload,
              first_seen_at = LEAST(manhwateca.external_releases.first_seen_at, EXCLUDED.first_seen_at),
              last_seen_at = GREATEST(manhwateca.external_releases.last_seen_at, EXCLUDED.last_seen_at),
              viewed_at = COALESCE(manhwateca.external_releases.viewed_at, EXCLUDED.viewed_at);

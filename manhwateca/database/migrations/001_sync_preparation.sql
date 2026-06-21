CREATE OR REPLACE FUNCTION manhwateca.touch_mangas_updated_at()
RETURNS trigger AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_mangas_updated_at
ON manhwateca.mangas;

CREATE TRIGGER trg_mangas_updated_at
BEFORE UPDATE ON manhwateca.mangas
FOR EACH ROW
EXECUTE FUNCTION manhwateca.touch_mangas_updated_at();

CREATE TABLE IF NOT EXISTS manhwateca.sync_events (
    id BIGSERIAL PRIMARY KEY,
    manga_id BIGINT REFERENCES manhwateca.mangas(id) ON DELETE SET NULL,
    notion_page_id VARCHAR(100),
    event_type VARCHAR(50) NOT NULL,
    sync_status VARCHAR(50) NOT NULL CHECK (
        sync_status IN ('pending', 'synced', 'error', 'ignored', 'conflict')
    ),
    direction VARCHAR(30) NOT NULL DEFAULT 'postgres_to_notion',
    message TEXT,
    payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMP NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_sync_events_manga_id
ON manhwateca.sync_events(manga_id);

CREATE INDEX IF NOT EXISTS idx_sync_events_status_created_at
ON manhwateca.sync_events(sync_status, created_at DESC);

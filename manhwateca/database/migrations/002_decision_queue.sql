CREATE TABLE IF NOT EXISTS manhwateca.decision_queue (
    id BIGSERIAL PRIMARY KEY,
    manga_id BIGINT REFERENCES manhwateca.mangas(id) ON DELETE SET NULL,
    decision_type VARCHAR(50) NOT NULL CHECK (
        decision_type IN (
            'mangaupdates_match',
            'duplicate_title',
            'notion_conflict',
            'metadata_conflict'
        )
    ),
    source VARCHAR(50) NOT NULL,
    source_key VARCHAR(200),
    title VARCHAR(500) NOT NULL,
    payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    resolution JSONB NOT NULL DEFAULT '{}'::jsonb,
    status VARCHAR(50) NOT NULL DEFAULT 'pending' CHECK (
        status IN ('pending', 'resolved', 'rejected', 'ignored')
    ),
    created_at TIMESTAMP NOT NULL DEFAULT now(),
    updated_at TIMESTAMP NOT NULL DEFAULT now(),
    resolved_at TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_decision_queue_status
ON manhwateca.decision_queue(status);

CREATE INDEX IF NOT EXISTS idx_decision_queue_type
ON manhwateca.decision_queue(decision_type);

CREATE INDEX IF NOT EXISTS idx_decision_queue_manga
ON manhwateca.decision_queue(manga_id);

CREATE INDEX IF NOT EXISTS idx_decision_queue_source
ON manhwateca.decision_queue(source);

CREATE INDEX IF NOT EXISTS idx_decision_queue_pending_lookup
ON manhwateca.decision_queue(decision_type, title, source, status);

CREATE TABLE IF NOT EXISTS manhwateca.flow_id_candidates (
    id BIGSERIAL PRIMARY KEY,
    execution_id VARCHAR(80) NOT NULL REFERENCES manhwateca.flow_executions(execution_id) ON DELETE CASCADE,
    work_id BIGINT REFERENCES manhwateca.mangas(id) ON DELETE SET NULL,
    searched_title TEXT NOT NULL,
    candidate_external_id TEXT,
    candidate_title TEXT,
    confidence NUMERIC,
    status VARCHAR(40) NOT NULL CHECK (
        status IN (
            'auto_matched',
            'pending_review',
            'not_found',
            'ignored',
            'error'
        )
    ),
    details JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMP NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_flow_id_candidates_execution
ON manhwateca.flow_id_candidates(execution_id, status, work_id);

CREATE INDEX IF NOT EXISTS idx_flow_id_candidates_work
ON manhwateca.flow_id_candidates(work_id, status);

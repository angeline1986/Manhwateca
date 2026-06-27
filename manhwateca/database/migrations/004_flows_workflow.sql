CREATE TABLE IF NOT EXISTS manhwateca.flow_executions (
    execution_id VARCHAR(80) PRIMARY KEY,
    status VARCHAR(50) NOT NULL CHECK (
        status IN (
            'idle',
            'validating',
            'running',
            'cancelling',
            'cancelled',
            'completed',
            'completed_with_warnings',
            'failed'
        )
    ),
    started_at TIMESTAMP,
    finished_at TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT now(),
    updated_at TIMESTAMP NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS manhwateca.flow_stage_executions (
    id BIGSERIAL PRIMARY KEY,
    execution_id VARCHAR(80) NOT NULL REFERENCES manhwateca.flow_executions(execution_id) ON DELETE CASCADE,
    stage VARCHAR(80) NOT NULL CHECK (
        stage IN (
            'organize_library',
            'catalog_works',
            'resolve_ids',
            'update_metadata',
            'sync_notion'
        )
    ),
    status VARCHAR(50) NOT NULL CHECK (
        status IN (
            'waiting',
            'validating',
            'running',
            'completed',
            'completed_with_warnings',
            'skipped',
            'failed',
            'cancelled'
        )
    ),
    progress_current INTEGER NOT NULL DEFAULT 0,
    progress_total INTEGER NOT NULL DEFAULT 0,
    elapsed_seconds INTEGER,
    estimated_remaining_seconds INTEGER,
    current_item TEXT,
    processed INTEGER NOT NULL DEFAULT 0,
    skipped INTEGER NOT NULL DEFAULT 0,
    metrics JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMP NOT NULL DEFAULT now(),
    updated_at TIMESTAMP NOT NULL DEFAULT now(),
    UNIQUE (execution_id, stage)
);

CREATE TABLE IF NOT EXISTS manhwateca.flow_messages (
    id BIGSERIAL PRIMARY KEY,
    execution_id VARCHAR(80) NOT NULL REFERENCES manhwateca.flow_executions(execution_id) ON DELETE CASCADE,
    stage VARCHAR(80),
    severity VARCHAR(20) NOT NULL CHECK (
        severity IN ('info', 'warning', 'error')
    ),
    code VARCHAR(100),
    message TEXT NOT NULL,
    details JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMP NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS manhwateca.flow_logs (
    id BIGSERIAL PRIMARY KEY,
    execution_id VARCHAR(80) NOT NULL REFERENCES manhwateca.flow_executions(execution_id) ON DELETE CASCADE,
    stage VARCHAR(80),
    operation VARCHAR(120) NOT NULL,
    status VARCHAR(50) NOT NULL,
    duration NUMERIC,
    processed INTEGER,
    error_code VARCHAR(100),
    message TEXT,
    details JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMP NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS manhwateca.flow_summaries (
    execution_id VARCHAR(80) PRIMARY KEY REFERENCES manhwateca.flow_executions(execution_id) ON DELETE CASCADE,
    metrics JSONB NOT NULL DEFAULT '{}'::jsonb,
    warnings_count INTEGER NOT NULL DEFAULT 0,
    errors_count INTEGER NOT NULL DEFAULT 0,
    updated_at TIMESTAMP NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_flow_executions_status
ON manhwateca.flow_executions(status);

CREATE INDEX IF NOT EXISTS idx_flow_executions_created_at
ON manhwateca.flow_executions(created_at DESC);

CREATE INDEX IF NOT EXISTS idx_flow_stage_execution
ON manhwateca.flow_stage_executions(execution_id, stage);

CREATE INDEX IF NOT EXISTS idx_flow_messages_execution
ON manhwateca.flow_messages(execution_id, stage, severity);

CREATE INDEX IF NOT EXISTS idx_flow_logs_execution
ON manhwateca.flow_logs(execution_id, stage, created_at);

ALTER TABLE manhwateca.flow_executions
ADD COLUMN IF NOT EXISTS current_stage VARCHAR(80),
ADD COLUMN IF NOT EXISTS progress JSONB NOT NULL DEFAULT '{}'::jsonb,
ADD COLUMN IF NOT EXISTS error_message TEXT,
ADD COLUMN IF NOT EXISTS summary JSONB NOT NULL DEFAULT '{}'::jsonb;

ALTER TABLE manhwateca.flow_stage_executions
ADD COLUMN IF NOT EXISTS progress JSONB NOT NULL DEFAULT '{}'::jsonb,
ADD COLUMN IF NOT EXISTS error_message TEXT;

ALTER TABLE manhwateca.flow_messages
ADD COLUMN IF NOT EXISTS level VARCHAR(20);

UPDATE manhwateca.flow_messages
SET level = severity
WHERE level IS NULL;

ALTER TABLE manhwateca.flow_logs
ADD COLUMN IF NOT EXISTS level VARCHAR(20),
ADD COLUMN IF NOT EXISTS event VARCHAR(120);

UPDATE manhwateca.flow_logs
SET level = status,
    event = operation
WHERE level IS NULL
   OR event IS NULL;

ALTER TABLE manhwateca.flow_summaries
ADD COLUMN IF NOT EXISTS status VARCHAR(50),
ADD COLUMN IF NOT EXISTS warnings JSONB NOT NULL DEFAULT '[]'::jsonb,
ADD COLUMN IF NOT EXISTS errors JSONB NOT NULL DEFAULT '[]'::jsonb,
ADD COLUMN IF NOT EXISTS created_at TIMESTAMP NOT NULL DEFAULT now();

CREATE TABLE IF NOT EXISTS manhwateca.flow_library_inventory (
    id BIGSERIAL PRIMARY KEY,
    execution_id VARCHAR(80) NOT NULL REFERENCES manhwateca.flow_executions(execution_id) ON DELETE CASCADE,
    work_name TEXT NOT NULL,
    source_path TEXT NOT NULL,
    destination_path TEXT,
    group_name TEXT,
    current_group TEXT,
    main_chapters INTEGER NOT NULL DEFAULT 0,
    side_chapters INTEGER NOT NULL DEFAULT 0,
    total_chapters INTEGER NOT NULL DEFAULT 0,
    is_valid BOOLEAN NOT NULL DEFAULT true,
    warnings JSONB NOT NULL DEFAULT '[]'::jsonb,
    metrics JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMP NOT NULL DEFAULT now(),
    updated_at TIMESTAMP NOT NULL DEFAULT now(),
    UNIQUE (execution_id, source_path)
);

CREATE INDEX IF NOT EXISTS idx_flow_library_inventory_execution
ON manhwateca.flow_library_inventory(execution_id, is_valid, work_name);

CREATE TABLE IF NOT EXISTS manhwateca.flow_file_normalization_plans (
    id BIGSERIAL PRIMARY KEY,
    execution_id TEXT NOT NULL REFERENCES manhwateca.flow_executions(execution_id) ON DELETE CASCADE,
    status TEXT NOT NULL,
    total_items INTEGER NOT NULL DEFAULT 0,
    total_conflicts INTEGER NOT NULL DEFAULT 0,
    total_errors INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    applied_at TIMESTAMPTZ,
    error_message TEXT
);

CREATE INDEX IF NOT EXISTS idx_flow_file_normalization_plans_execution
ON manhwateca.flow_file_normalization_plans(execution_id, created_at DESC);

CREATE TABLE IF NOT EXISTS manhwateca.flow_file_normalization_items (
    id BIGSERIAL PRIMARY KEY,
    plan_id BIGINT NOT NULL REFERENCES manhwateca.flow_file_normalization_plans(id) ON DELETE CASCADE,
    execution_id TEXT NOT NULL REFERENCES manhwateca.flow_executions(execution_id) ON DELETE CASCADE,
    inventory_issue_id BIGINT REFERENCES manhwateca.flow_library_inventory_issues(id) ON DELETE SET NULL,
    work_title TEXT NOT NULL,
    original_path TEXT NOT NULL,
    proposed_path TEXT NOT NULL,
    operation TEXT NOT NULL,
    status TEXT NOT NULL,
    severity TEXT NOT NULL DEFAULT 'info',
    message TEXT,
    details JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    applied_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_flow_file_normalization_items_plan
ON manhwateca.flow_file_normalization_items(plan_id, status);

CREATE INDEX IF NOT EXISTS idx_flow_file_normalization_items_execution
ON manhwateca.flow_file_normalization_items(execution_id, status, operation);

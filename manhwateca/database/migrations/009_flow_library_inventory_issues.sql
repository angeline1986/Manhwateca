CREATE TABLE IF NOT EXISTS manhwateca.flow_library_inventory_issues (
    id BIGSERIAL PRIMARY KEY,
    execution_id VARCHAR(80) NOT NULL REFERENCES manhwateca.flow_executions(execution_id) ON DELETE CASCADE,
    inventory_id BIGINT REFERENCES manhwateca.flow_library_inventory(id) ON DELETE CASCADE,
    work_title TEXT NOT NULL,
    relative_path TEXT NOT NULL,
    file_name TEXT NOT NULL,
    issue_type VARCHAR(80) NOT NULL,
    severity VARCHAR(20) NOT NULL CHECK (
        severity IN ('info', 'warning', 'error')
    ),
    message TEXT NOT NULL,
    suggestion TEXT,
    details JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMP NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_flow_library_inventory_issues_execution
ON manhwateca.flow_library_inventory_issues(execution_id, issue_type, severity);

CREATE INDEX IF NOT EXISTS idx_flow_library_inventory_issues_inventory
ON manhwateca.flow_library_inventory_issues(inventory_id);

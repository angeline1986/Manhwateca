CREATE TABLE IF NOT EXISTS manhwateca.system_audit_logs (
    id BIGSERIAL PRIMARY KEY,

    occurred_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),

    actor TEXT NOT NULL DEFAULT 'system',
    session_id TEXT NULL,
    request_id TEXT NULL,

    module TEXT NOT NULL,
    action TEXT NOT NULL,

    entity_type TEXT NULL,
    entity_id TEXT NULL,

    status TEXT NOT NULL DEFAULT 'success'
        CHECK (status IN ('success', 'warning', 'error')),

    severity TEXT NOT NULL DEFAULT 'info'
        CHECK (severity IN ('debug', 'info', 'warning', 'error')),

    duration_ms INTEGER NULL CHECK (duration_ms IS NULL OR duration_ms >= 0),

    message TEXT NULL,
    details JSONB NOT NULL DEFAULT '{}'::jsonb
);

CREATE INDEX IF NOT EXISTS idx_system_audit_logs_occurred_at
ON manhwateca.system_audit_logs (occurred_at DESC);

CREATE INDEX IF NOT EXISTS idx_system_audit_logs_module_action
ON manhwateca.system_audit_logs (module, action);

CREATE INDEX IF NOT EXISTS idx_system_audit_logs_entity
ON manhwateca.system_audit_logs (entity_type, entity_id);

CREATE INDEX IF NOT EXISTS idx_system_audit_logs_status
ON manhwateca.system_audit_logs (status);

CREATE INDEX IF NOT EXISTS idx_system_audit_logs_request_id
ON manhwateca.system_audit_logs (request_id);

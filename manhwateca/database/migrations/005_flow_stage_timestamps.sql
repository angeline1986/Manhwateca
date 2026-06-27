ALTER TABLE manhwateca.flow_stage_executions
ADD COLUMN IF NOT EXISTS started_at TIMESTAMP;

ALTER TABLE manhwateca.flow_stage_executions
ADD COLUMN IF NOT EXISTS finished_at TIMESTAMP;

ALTER TABLE manhwateca.release_monitor_subscriptions
ADD COLUMN IF NOT EXISTS favorite BOOLEAN NOT NULL DEFAULT FALSE;

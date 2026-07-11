CREATE TABLE IF NOT EXISTS scheduler_locks
(
    lock_name VARCHAR(150) PRIMARY KEY,
    owner_token VARCHAR(36) NOT NULL,
    acquired_at TIMESTAMP NOT NULL,
    heartbeat_at TIMESTAMP NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP NOT NULL
        DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS
idx_scheduler_locks_expires_at
ON scheduler_locks(expires_at);

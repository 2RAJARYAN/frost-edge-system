PRAGMA journal_mode = WAL;

CREATE TABLE IF NOT EXISTS readings (
    id    INTEGER PRIMARY KEY AUTOINCREMENT,
    ts    TEXT NOT NULL,        -- ISO 8601 UTC, e.g. 2026-08-20T13:24:41Z
    key   TEXT NOT NULL,        -- matches SensorReader dict keys exactly, e.g. "temperature_c"
    value REAL NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_readings_key_ts ON readings(key, ts);

CREATE TABLE IF NOT EXISTS predictions (
    id                   INTEGER PRIMARY KEY AUTOINCREMENT,
    ts                   TEXT NOT NULL,
    predicted_min_temp_c REAL,          -- regression output (regression-then-threshold, per Feasibility Study §2.2)
    risk_score           REAL NOT NULL, -- 0.0-1.0, derived from the above
    model_version        TEXT NOT NULL  -- which model artifact produced this — matters once Repo A ships v2, v3...
);
CREATE INDEX IF NOT EXISTS idx_predictions_ts ON predictions(ts);

CREATE TABLE IF NOT EXISTS alerts_sent (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    ts         TEXT NOT NULL,
    channel    TEXT NOT NULL,             -- "telegram" / "sms" — matches AlertChannel implementations
    risk_score REAL NOT NULL,             -- the score that triggered this alert
    message    TEXT NOT NULL,
    status     TEXT NOT NULL DEFAULT 'sent'  -- 'sent' / 'failed' — Phase 4 failure-mode testing needs this
);
CREATE INDEX IF NOT EXISTS idx_alerts_sent_channel_ts ON alerts_sent(channel, ts);


SCHEMA = """

CREATE TABLE IF NOT EXISTS investigations (

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    station_id TEXT NOT NULL,

    station_latitude REAL,
    station_longitude REAL,

    status TEXT NOT NULL,

    current_stage TEXT NOT NULL DEFAULT 'pending',

    execution_seconds REAL,

    created_at TEXT NOT NULL,

    updated_at TEXT,

    error_message TEXT,

    result_json TEXT,

    checkpoint_json TEXT

);


CREATE TABLE IF NOT EXISTS mcp_tool_metrics (

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    investigation_id INTEGER NOT NULL,

    tool_name TEXT NOT NULL,

    calls INTEGER NOT NULL DEFAULT 0,

    attempts INTEGER NOT NULL DEFAULT 0,

    successes INTEGER NOT NULL DEFAULT 0,

    failures INTEGER NOT NULL DEFAULT 0,

    retries INTEGER NOT NULL DEFAULT 0,

    total_duration_seconds REAL NOT NULL DEFAULT 0,

    last_duration_seconds REAL NOT NULL DEFAULT 0,

    FOREIGN KEY (investigation_id)
        REFERENCES investigations(id)
        ON DELETE CASCADE

);


CREATE TABLE IF NOT EXISTS investigation_checkpoints (

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    investigation_id INTEGER NOT NULL,

    stage TEXT NOT NULL,

    state_json TEXT NOT NULL,

    created_at TEXT NOT NULL,

    FOREIGN KEY (investigation_id)
        REFERENCES investigations(id)
        ON DELETE CASCADE

);


CREATE TABLE IF NOT EXISTS investigation_approvals (

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    investigation_id INTEGER NOT NULL UNIQUE,

    decision TEXT NOT NULL
        CHECK (decision IN ('approved', 'rejected')),

    reviewer TEXT NOT NULL,

    comments TEXT,

    decided_at TEXT NOT NULL,

    FOREIGN KEY (investigation_id)
        REFERENCES investigations(id)
        ON DELETE CASCADE

);

"""
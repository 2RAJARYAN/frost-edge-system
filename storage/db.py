import sqlite3
from contextlib import contextmanager
from pathlib import Path

DEFAULT_DB_PATH = Path(__file__).parent.parent / "frost_edge.db"


@contextmanager
def get_connection(db_path: str | Path = DEFAULT_DB_PATH):
    """Yields a SQLite connection with settings safe for our
    multi-process (4 systemd services) access pattern.

    Every caller goes through this — never open sqlite3.connect()
    directly elsewhere in the codebase, or you lose the busy_timeout
    below and reintroduce the "database is locked" risk WAL alone
    doesn't fully remove.
    """
    conn = sqlite3.connect(db_path, timeout=5.0)
    conn.execute("PRAGMA busy_timeout = 5000")
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db(db_path: str | Path = DEFAULT_DB_PATH):
    schema_path = Path(__file__).parent / "schema.sql"
    with get_connection(db_path) as conn:
        conn.executescript(schema_path.read_text())


def insert_reading(ts: str, key: str, value: float, db_path: str | Path = DEFAULT_DB_PATH):
    with get_connection(db_path) as conn:
        conn.execute(
            "INSERT INTO readings (ts, key, value) VALUES (?, ?, ?)",
            (ts, key, value),
        )


def insert_readings_batch(ts: str, values: dict, db_path: str | Path = DEFAULT_DB_PATH):
    """One poll tick -> one row per key, single transaction.

    This is what actually consumes a SensorReader.read() dict directly
    -- ts stamped once here, not by the reader. Batches all keys from
    one tick into a single commit rather than N separate ones, so a
    crash mid-tick can't leave temperature_c written but humidity_pct
    missing for the same timestamp.
    """
    with get_connection(db_path) as conn:
        conn.executemany(
            "INSERT INTO readings (ts, key, value) VALUES (?, ?, ?)",
            [(ts, key, value) for key, value in values.items()],
        )


def latest_readings(db_path: str | Path = DEFAULT_DB_PATH) -> dict:
    """Most recent value per key -- what the dashboard shows as
    'current conditions'."""
    with get_connection(db_path) as conn:
        rows = conn.execute(
            """
            SELECT key, value FROM readings r
            WHERE ts = (SELECT MAX(ts) FROM readings WHERE key = r.key)
            """
        ).fetchall()
    return {key: value for key, value in rows}

from storage.db import init_db, insert_reading, insert_readings_batch, latest_readings


def test_init_db_creates_tables(tmp_path):
    db_path = tmp_path / "test.db"
    init_db(db_path)
    assert db_path.exists()


def test_insert_and_read_single_value(tmp_path):
    db_path = tmp_path / "test.db"
    init_db(db_path)
    insert_reading("2026-08-20T10:00:00Z", "temperature_c", 3.5, db_path=db_path)
    assert latest_readings(db_path) == {"temperature_c": 3.5}


def test_batch_insert_writes_all_keys_from_one_tick(tmp_path):
    db_path = tmp_path / "test.db"
    init_db(db_path)
    insert_readings_batch(
        "2026-08-20T10:00:00Z",
        {"temperature_c": 3.5, "humidity_pct": 81.0},
        db_path=db_path,
    )
    assert latest_readings(db_path) == {"temperature_c": 3.5, "humidity_pct": 81.0}


def test_latest_readings_returns_most_recent_per_key(tmp_path):
    db_path = tmp_path / "test.db"
    init_db(db_path)
    insert_reading("2026-08-20T10:00:00Z", "temperature_c", 3.5, db_path=db_path)
    insert_reading("2026-08-20T10:15:00Z", "temperature_c", 4.1, db_path=db_path)
    assert latest_readings(db_path) == {"temperature_c": 4.1}


def test_latest_readings_empty_db_returns_empty_dict(tmp_path):
    db_path = tmp_path / "test.db"
    init_db(db_path)
    assert latest_readings(db_path) == {}

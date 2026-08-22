import pytest

from dashboard.app import create_app
from storage.db import get_connection, init_db, insert_reading, insert_readings_batch


@pytest.fixture
def db_path(tmp_path):
    """A freshly-initialized, empty SQLite db file, unique per test."""
    path = tmp_path / "test.db"
    init_db(path)
    return str(path)


@pytest.fixture
def client(db_path):
    """Flask test client wired to the db_path fixture above -- any
    test that also asks for `db_path` gets the exact same database
    the client is reading from, so inserts and requests line up."""
    app = create_app({"storage": {"db_path": db_path}})
    app.config["TESTING"] = True
    return app.test_client()


def test_index_serves_html(client):
    response = client.get("/")
    assert response.status_code == 200
    assert b"Frost Edge" in response.data


def test_api_latest_empty_db_returns_no_readings_no_prediction(client):
    response = client.get("/api/latest")
    data = response.get_json()
    assert data["readings"] == {}
    assert data["prediction"] is None


def test_api_latest_returns_current_readings(client, db_path):
    insert_readings_batch(
        "2026-08-22T06:00:00Z",
        {"temperature_c": 2.5, "humidity_pct": 85.0},
        db_path=db_path,
    )
    response = client.get("/api/latest")
    data = response.get_json()
    assert data["readings"] == {"temperature_c": 2.5, "humidity_pct": 85.0}


def test_api_latest_returns_most_recent_prediction(client, db_path):
    # No inference module exists yet, so this is the only way to get a
    # row into `predictions` for testing -- same idea as engineering a
    # real SensorReadError in test_poller.py rather than mocking one.
    with get_connection(db_path) as conn:
        conn.execute(
            "INSERT INTO predictions (ts, predicted_min_temp_c, risk_score, model_version) "
            "VALUES (?, ?, ?, ?)",
            ("2026-08-22T06:00:00Z", 1.2, 0.42, "stub-v0"),
        )
    response = client.get("/api/latest")
    data = response.get_json()
    assert data["prediction"]["risk_score"] == 0.42
    assert data["prediction"]["model_version"] == "stub-v0"


def test_api_history_returns_rows_oldest_first(client, db_path):
    insert_reading("2026-08-22T06:00:00Z", "temperature_c", 2.5, db_path=db_path)
    insert_reading("2026-08-22T06:01:00Z", "temperature_c", 3.0, db_path=db_path)
    response = client.get("/api/history/temperature_c")
    data = response.get_json()
    assert [row["value"] for row in data] == [2.5, 3.0]


def test_api_history_unknown_key_returns_empty_list(client):
    response = client.get("/api/history/does_not_exist")
    assert response.get_json() == []

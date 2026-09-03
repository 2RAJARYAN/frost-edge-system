import pytest

from sensors.mock_sensor import MockSensorReader
from sensors.poller import build_reader, poll_once
from storage.db import init_db, latest_readings


def test_build_reader_returns_mock_when_configured():
    config = {"sensor_backend": "mock", "mock": {"csv_path": None, "loop": True}}
    reader = build_reader(config)
    assert isinstance(reader, MockSensorReader)


def test_build_reader_raises_on_real_backend_not_yet_implemented():
    config = {"sensor_backend": "real"}
    with pytest.raises(NotImplementedError):
        build_reader(config)


def test_build_reader_raises_on_unknown_backend():
    config = {"sensor_backend": "bluetooth"}
    with pytest.raises(ValueError):
        build_reader(config)


def test_poll_once_writes_reading_to_db(tmp_path):
    db_path = str(tmp_path / "test.db")
    init_db(db_path)
    reader = MockSensorReader()

    result = poll_once(reader, db_path)

    assert result is not None
    assert latest_readings(db_path) == result


def test_poll_once_returns_none_on_sensor_failure(tmp_path):
    db_path = str(tmp_path / "test.db")
    init_db(db_path)
    # loop=False + immediately-exhausted CSV forces a SensorReadError on read()
    csv_file = tmp_path / "one_row.csv"
    csv_file.write_text("temperature_c\n1.0\n")
    reader = MockSensorReader(csv_path=str(csv_file), loop=False)
    reader.read()  # consume the only row

    result = poll_once(reader, db_path)

    assert result is None
    assert latest_readings(db_path) == {}  # nothing written on failure

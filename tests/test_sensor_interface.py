import pytest
from sensors.base import SensorReader, SensorReadError
from sensors.mock_sensor import MockSensorReader


def test_mock_reader_conforms_to_interface():
    reader = MockSensorReader()
    assert isinstance(reader, SensorReader)


def test_synthetic_read_returns_expected_keys_and_types():
    reader = MockSensorReader()
    reading = reader.read()
    assert isinstance(reading, dict)
    for key in ("temperature_c", "humidity_pct", "pressure_hpa"):
        assert key in reading
        assert isinstance(reading[key], float)


def test_missing_csv_path_raises():
    with pytest.raises(FileNotFoundError):
        MockSensorReader(csv_path="does/not/exist.csv")


def test_empty_csv_raises(tmp_path):
    csv_file = tmp_path / "empty.csv"
    csv_file.write_text("temperature_c\n")  # header only, no data rows
    with pytest.raises(ValueError):
        MockSensorReader(csv_path=str(csv_file))


def test_csv_replay_reads_rows_in_order(tmp_path):
    csv_file = tmp_path / "sample.csv"
    csv_file.write_text(
        "temperature_c,humidity_pct\n"
        "1.5,80.0\n"
        "2.5,78.0\n"
    )
    reader = MockSensorReader(csv_path=str(csv_file), loop=False)
    assert reader.read() == {"temperature_c": 1.5, "humidity_pct": 80.0}
    assert reader.read() == {"temperature_c": 2.5, "humidity_pct": 78.0}


def test_csv_replay_raises_when_exhausted_and_not_looping(tmp_path):
    csv_file = tmp_path / "sample.csv"
    csv_file.write_text("temperature_c\n1.0\n")
    reader = MockSensorReader(csv_path=str(csv_file), loop=False)
    reader.read()
    with pytest.raises(SensorReadError):
        reader.read()


def test_csv_replay_loops_when_enabled(tmp_path):
    csv_file = tmp_path / "sample.csv"
    csv_file.write_text("temperature_c\n1.0\n2.0\n")
    reader = MockSensorReader(csv_path=str(csv_file), loop=True)
    reader.read()
    reader.read()
    assert reader.read() == {"temperature_c": 1.0}  # wraps back to row 0

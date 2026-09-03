import logging
import time
from datetime import UTC, datetime

from config.loader import load_config
from sensors.base import SensorReader, SensorReadError
from sensors.mock_sensor import MockSensorReader
from storage.db import init_db, insert_readings_batch

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("frost-sensors")


def build_reader(config: dict) -> SensorReader:
    """Config decides the concrete class -- Dependency Inversion (§8.2),
    now actually doing something instead of just being an interface."""
    backend = config["sensor_backend"]
    if backend == "mock":
        mock_cfg = config.get("mock", {})
        return MockSensorReader(
            csv_path=mock_cfg.get("csv_path"),
            loop=mock_cfg.get("loop", True),
        )
    elif backend == "real":
        raise NotImplementedError(
            "Real sensor drivers not built yet -- set sensor_backend: mock in config.yaml"
        )
    else:
        raise ValueError(f"Unknown sensor_backend: {backend!r}")


def poll_once(reader: SensorReader, db_path: str) -> dict | None:
    """One tick: read, stamp, persist. Returns the reading, or None if
    the sensor failed this tick -- a bad read doesn't crash the loop,
    it just gets logged and skipped."""
    try:
        reading = reader.read()
    except SensorReadError as e:
        logger.warning("Sensor read failed, skipping this tick: %s", e)
        return None

    ts = datetime.now(UTC).isoformat()
    insert_readings_batch(ts, reading, db_path=db_path)
    logger.info("Wrote reading at %s: %s", ts, reading)
    return reading


def run(config_path: str | None = None):
    config = load_config(config_path) if config_path else load_config()
    db_path = config["storage"]["db_path"]
    interval = config["poll_interval_seconds"]

    init_db(db_path)
    reader = build_reader(config)

    logger.info(
        "frost-sensors starting: backend=%s interval=%ss db=%s",
        config["sensor_backend"],
        interval,
        db_path,
    )

    while True:
        poll_once(reader, db_path)
        time.sleep(interval)


if __name__ == "__main__":
    run()

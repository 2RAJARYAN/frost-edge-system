import csv
import random
from pathlib import Path

from sensors.base import SensorReader, SensorReadError


class MockSensorReader(SensorReader):
    """Replays historical readings from a CSV, one row per call.

    No CSV yet? Falls back to synthetic-but-plausible values instead
    of blocking Repo B's build on Repo A's dataset. Once your teammate
    shares real data, pass csv_path and nothing downstream changes.
    """

    def __init__(self, csv_path: str | None = None, loop: bool = True):
        self._loop = loop
        self._rows: list[dict] = []
        self._index = 0

        if csv_path is not None:
            path = Path(csv_path)
            if not path.exists():
                raise FileNotFoundError(f"Mock data file not found: {csv_path}")
            with path.open(newline="") as f:
                self._rows = [
                    {k: float(v) for k, v in row.items()} for row in csv.DictReader(f)
                ]
            if not self._rows:
                raise ValueError(f"Mock data file is empty: {csv_path}")

    def read(self) -> dict:
        if self._rows:
            return self._read_from_csv()
        return self._read_synthetic()

    def _read_from_csv(self) -> dict:
        if self._index >= len(self._rows):
            if self._loop:
                self._index = 0
            else:
                raise SensorReadError("Mock CSV exhausted and loop=False")
        row = self._rows[self._index]
        self._index += 1
        return row

    def _read_synthetic(self) -> dict:
        return {
            "temperature_c": round(random.uniform(2.0, 15.0), 2),
            "humidity_pct": round(random.uniform(40.0, 90.0), 2),
            "pressure_hpa": round(random.uniform(995.0, 1025.0), 2),
        }

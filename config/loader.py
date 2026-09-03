from pathlib import Path
import yaml

DEFAULT_CONFIG_PATH = Path(__file__).parent / "config.yaml"

VALID_SENSOR_BACKENDS = ("mock", "real")


class ConfigError(Exception):
    """Raised on missing or malformed config -- meant to fail loudly
    at startup, not deep inside a running service."""

    pass


def load_config(path: str | Path = DEFAULT_CONFIG_PATH) -> dict:
    path = Path(path)
    if not path.exists():
        raise ConfigError(
            f"Config file not found at {path}. "
            "Copy config/config.example.yaml to config/config.yaml "
            "and fill in real values."
        )
    with path.open() as f:
        config = yaml.safe_load(f)
    _validate(config)
    return config


def _validate(config: dict):
    required_top_level = ["sensor_backend", "poll_interval_seconds", "storage"]
    missing = [k for k in required_top_level if k not in config]
    if missing:
        raise ConfigError(f"config.yaml missing required keys: {missing}")

    if config["sensor_backend"] not in VALID_SENSOR_BACKENDS:
        raise ConfigError(
            f"sensor_backend must be one of {VALID_SENSOR_BACKENDS}, "
            f"got {config['sensor_backend']!r}"
        )

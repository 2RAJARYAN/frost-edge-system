from pathlib import Path
import yaml
#for load token form .env
import os 
from pathlib import Path
from dotenv import load_dotenv


DEFAULT_CONFIG_PATH = Path(__file__).parent / "config.yaml"

VALID_SENSOR_BACKENDS = ("mock", "real")


class ConfigError(Exception):
    """Raised on missing or malformed config -- meant to fail loudly
    at startup, not deep inside a running service."""


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

def load_env():
    """
    Load .env file loacated to project root.
    """
    project_root=Path(__file__).resolve().parents[1]  # go up to reporoot
    dotenv_path=project_root/".env"

    if dotenv_path.is_file():   #<--check path points to actual file.
        load_dotenv(dotenv_path)
        print(f".env loaded from {dotenv_path}")
    else:
        print("no .env file found ")

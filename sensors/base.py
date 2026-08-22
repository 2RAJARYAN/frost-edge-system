from abc import ABC, abstractmethod


class SensorReadError(Exception):
    """Raised when a sensor fails to produce a valid reading.

    The polling service catches this specifically so one failed sensor
    doesn't take down the whole loop, and — just as important — doesn't
    get silently logged as a 0.0 or None that flows straight into the
    model as if it were real data.
    """
    pass


class SensorReader(ABC):
    """The one contract every sensor driver, real or mock, must satisfy."""

    @abstractmethod
    def read(self) -> dict:
        """Return one reading as flat dict: value name -> float.

        Contract:
        - Keys are lowercase, unit-suffixed strings, e.g. "temperature_c",
          "humidity_pct". Every driver measuring the same physical
          quantity uses the same key + unit, so feature_pipeline.py
          doesn't care which sensor produced a given row.
        - No timestamp in here — the caller stamps it at write time.
          A reader's job is "what does the sensor say right now", not
          "when did I ask" — see Single Responsibility note below.
        - Raises SensorReadError on failure (disconnected, bad
          checksum, I2C timeout). Never returns None or a fabricated
          zero.
        """
        raise NotImplementedError


class AlertSendError(Exception):
    """Raised when a channel fails to deliver a message.

    Caught per-channel by whatever dispatches alerts, so one broken
    channel (SMS API down) doesn't stop others from firing -- the
    same fault-isolation instinct as the four-service architecture,
    one level down.
    """
    pass


class AlertChannel(ABC):
    """The contract every notification channel -- console, Telegram,
    SMS, future WhatsApp -- must satisfy."""

    @abstractmethod
    def send(self, message: str) -> None:
        """Deliver `message`. Raise AlertSendError on failure -- never
        fail silently, never return a bool that's easy to ignore."""
        raise NotImplementedError

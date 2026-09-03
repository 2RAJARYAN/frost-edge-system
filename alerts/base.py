from abc import ABC, abstractmethod


class AlertSendError(Exception):
    """Raised when a channel fails to deliver a message.

    Caught per-channel by whatever dispatches alerts, so one broken
    channel (SMS API down) doesn't stop others from firing -- the
    same fault-isolation instinct as the four-service architecture,
    one level down.
    """


class AlertChannel(ABC):
    """The contract every notification channel -- console, Telegram,
    SMS, future WhatsApp -- must satisfy."""

    @abstractmethod
    def send(self, message: str) -> None:
        """Deliver `message`. Raise AlertSendError on failure -- never
        fail silently, never return a bool that's easy to ignore."""
        raise NotImplementedError

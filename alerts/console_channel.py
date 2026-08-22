import logging

from alerts.base import AlertChannel

logger = logging.getLogger("alerts.console")


class ConsoleAlertChannel(AlertChannel):
    def __init__(self, name: str = "console"):
        self.name = name

    def send(self, message: str) -> None:
        logger.info("[%s ALERT] %s", self.name.upper(), message)

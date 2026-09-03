"""
Owner: your teammate -- real Telegram Bot API integration goes here.

Contract (see alerts/base.py -- must be a drop-in AlertChannel, no
other file should need to change once this is filled in):

    __init__(self, bot_token: str, chat_id: str)
        From config.yaml's `telegram:` section.

    send(self, message: str) -> None
        POST to https://api.telegram.org/bot<bot_token>/sendMessage
        with JSON body {"chat_id": chat_id, "text": message}.
        On any non-2xx response, timeout, or network error, raise
        AlertSendError -- never let a raw `requests` exception escape,
        the dispatcher only knows how to handle AlertSendError.

Stretch goal (Phase 4+, Feasibility Study §2.3): bidirectional
"status" command. That's a separate listener process, not part of
this class -- needs its own systemd unit to fit the architecture.

Until implemented, keep config.yaml's alerts.channels as [console]
so nothing downstream breaks.
"""

from alerts.base import AlertChannel


class TelegramAlertChannel(AlertChannel):
    def __init__(self, bot_token: str, chat_id: str):
        self.bot_token = bot_token
        self.chat_id = chat_id

    def send(self, message: str) -> None:
        raise NotImplementedError(
            "TelegramAlertChannel.send() not implemented yet -- "
            "see module docstring for the contract to build against."
        )

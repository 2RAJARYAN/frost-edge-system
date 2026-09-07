from __future__ import annotations

from alerts.base import AlertChannel ,AlertSendError
import requests

import logging 
from typing import Final

# add logger help in debugging task.
log:Final =logging.getLogger(__name__)

class TelegramAlertChannel(AlertChannel):
    """
    concrete `AlertChannel` that send plain text message via the telegram bot api.

    Parameters --> bot_token:str,chat_id:str|int

    """
    def __init__(self, bot_token: str, chat_id: str|int)->None:
        if not bot_token:
            raise ValueError("telegram bot token must be non empty string")
        if not chat_id:
            raise ValueError("Telegram chat_id must be provided")
        
        #base url is constant for the bot api.
        self.base_url:str=f"https://api.telegram.org/bot{bot_token}"
        self.chat_id:str=str(chat_id)
        
        log.debug(
            "telegraAlertChannel initialised base_url=%s,chat_id=%s",self.base_url,self.chat_id,
            )

    def send(self, message: str) -> None:

        """
        Post ``/sendMessage`` to the telegram bot api.
        this block for up to the ``timeout`` define on the request(10 seconds).On any non 200 responce we raise 
        ``AlertSendError`` - the dispatcher catches this per channel and records a "failed" status in the db.
        Parameters -- message:str (the raw text to deliver , telgram will render markdown style.).
        """
        payload={
            "chat_id":self.chat_id,
            "text":message,
            # "parse_mode":"MarkdownV2" 
        }
        try:
            resp=requests.post(
                f"{self.base_url}/sendMessage",
                json=payload,
                timeout=10,  #in seconds.
            )
        except requests.RequestException as exc:
            raise AlertSendError(f"telegram request failed :{exc}") from exc

        #telegram return JSON with a top-level ``ok`` flag.
        if not resp.ok:
            # return json with an ``description`` field
            try:
                detail=resp.json().get("description",resp.text)
            except Exception:
                detail=resp.text
            raise AlertSendError(
                f"telegram api error {resp.status_code}:{detail}"
            )

        log.info("telegram message sent (chat_id%s)",self.chat_id)


























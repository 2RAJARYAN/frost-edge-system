import os
from unittest.mock import patch
import pytest
from alerts.dispatcher import build_channels

def test_telegram_from_env(monkeypatch):
    # Simulate .env values
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "fake-token")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "12345")
    cfg = {"alerts": {"channels": ["telegram"]}, "telegram": {}}
    channels = build_channels(cfg)

    assert "telegram" in channels
    # The channel instance should have the values we set
    tg = channels["telegram"]
    assert tg.base_url.endswith("fake-token")
    assert tg.chat_id == "12345"
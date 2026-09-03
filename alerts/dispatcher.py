import logging
import time
from datetime import datetime, timezone

from alerts.alert_policy import AlertPolicy
from alerts.base import AlertChannel
from alerts.console_channel import ConsoleAlertChannel
from alerts.sms_gateway import SmsAlertChannel
from alerts.telegram_bot import TelegramAlertChannel
from config.loader import load_config
from storage.db import init_db, insert_alert_sent, latest_prediction

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("frost-alerts")


def build_channels(config: dict) -> dict[str, AlertChannel]:
    """Config decides which concrete channels run -- same
    Dependency Inversion pattern as build_reader() in the poller."""
    names = config.get("alerts", {}).get("channels", ["console"])
    channels: dict[str, AlertChannel] = {}
    for name in names:
        if name == "console":
            channels[name] = ConsoleAlertChannel()
        elif name == "telegram":
            tg = config["telegram"]
            channels[name] = TelegramAlertChannel(tg["bot_token"], tg["chat_id"])
        elif name == "sms":
            sms = config["sms"]
            channels[name] = SmsAlertChannel(sms["api_key"], sms["api_url"], sms["to_number"])
        else:
            raise ValueError(f"Unknown alert channel: {name!r}")
    return channels


def _build_message(prediction: dict, decision) -> str:
    return (
        f"FROST RISK ALERT — score {prediction['risk_score']:.2f} "
        f"(predicted min {prediction['predicted_min_temp_c']}°C, "
        f"model {prediction['model_version']}). {decision.reason}"
    )


def evaluate_and_dispatch(prediction: dict | None, policy: AlertPolicy, channels: dict,
                            db_path: str, now: float | None = None):
    """One decision point: given the latest prediction, ask the policy,
    and if it says send, fire every channel. Returns the AlertDecision,
    or None if there was nothing to evaluate.

    Separated from run()'s loop for the same reason poll_once() was
    separated from the poller's loop -- this is the part with real
    logic, and it needs to be testable without sleeping or threads.
    """
    if prediction is None:
        return None

    decision = policy.evaluate(prediction["risk_score"], now=now)
    if not decision.should_send:
        return decision

    message = _build_message(prediction, decision)
    ts = datetime.now(timezone.utc).isoformat()

    for name, channel in channels.items():
        # Broad except is deliberate here, not sloppy -- this loop IS
        # the fault-isolation boundary from the architecture table,
        # one level deeper: a broken/unfinished channel (a stub still
        # raising NotImplementedError, a real bug in a teammate's
        # Telegram code, a network timeout) must never crash the whole
        # alerts service or stop OTHER channels from firing.
        try:
            channel.send(message)
            status = "sent"
        except Exception as e:
            logger.warning("Channel '%s' failed: %s: %s", name, type(e).__name__, e)
            status = "failed"
        insert_alert_sent(ts, name, prediction["risk_score"], message, status, db_path)

    logger.info("Dispatched alert (%s): %s", decision.reason, message)
    return decision


def run(config_path: str | None = None):
    config = load_config(config_path) if config_path else load_config()
    db_path = config["storage"]["db_path"]
    alert_cfg = config["alerts"]

    init_db(db_path)
    policy = AlertPolicy(
        risk_threshold=alert_cfg["risk_threshold"],
        hysteresis_margin=alert_cfg["hysteresis_margin"],
        cooldown_minutes=alert_cfg["cooldown_minutes"],
    )
    channels = build_channels(config)
    logger.info("frost-alerts starting: channels=%s", list(channels.keys()))

    last_processed_ts = None
    while True:
        prediction = latest_prediction(db_path)
        if prediction is not None and prediction["ts"] != last_processed_ts:
            last_processed_ts = prediction["ts"]
            evaluate_and_dispatch(prediction, policy, channels, db_path)
        time.sleep(config["poll_interval_seconds"])


if __name__ == "__main__":
    run()

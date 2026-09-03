import pytest

from alerts.alert_policy import AlertPolicy
from alerts.base import AlertChannel, AlertSendError
from alerts.console_channel import ConsoleAlertChannel
from alerts.dispatcher import build_channels, evaluate_and_dispatch
from storage.db import get_connection, init_db


class FailingChannel(AlertChannel):
    """Test double simulating a broken channel -- e.g. an unfinished
    stub, or a real network failure -- to prove the dispatcher isolates
    it rather than crashing."""
    def send(self, message: str) -> None:
        raise AlertSendError("simulated failure")


@pytest.fixture
def db_path(tmp_path):
    path = str(tmp_path / "test.db")
    init_db(path)
    return path


@pytest.fixture
def policy():
    return AlertPolicy(risk_threshold=0.6, hysteresis_margin=0.1, cooldown_minutes=30)


def test_build_channels_defaults_to_console():
    channels = build_channels({})
    assert list(channels.keys()) == ["console"]
    assert isinstance(channels["console"], ConsoleAlertChannel)


def test_build_channels_rejects_unknown_name():
    with pytest.raises(ValueError):
        build_channels({"alerts": {"channels": ["carrier_pigeon"]}})


def test_no_prediction_returns_none(policy, db_path):
    result = evaluate_and_dispatch(None, policy, {}, db_path)
    assert result is None


def test_below_threshold_sends_nothing(policy, db_path):
    prediction = {"risk_score": 0.2, "predicted_min_temp_c": 5.0, "model_version": "stub-v0"}
    decision = evaluate_and_dispatch(prediction, policy, {"console": ConsoleAlertChannel()}, db_path)
    assert decision.should_send is False
    with get_connection(db_path) as conn:
        count = conn.execute("SELECT COUNT(*) FROM alerts_sent").fetchone()[0]
    assert count == 0


def test_above_threshold_dispatches_and_logs(policy, db_path):
    prediction = {"risk_score": 0.8, "predicted_min_temp_c": -1.0, "model_version": "stub-v0"}
    decision = evaluate_and_dispatch(
        prediction, policy, {"console": ConsoleAlertChannel()}, db_path, now=0,
    )
    assert decision.should_send is True
    with get_connection(db_path) as conn:
        row = conn.execute("SELECT channel, status FROM alerts_sent").fetchone()
    assert row == ("console", "sent")


def test_one_broken_channel_does_not_block_others(policy, db_path):
    prediction = {"risk_score": 0.8, "predicted_min_temp_c": -1.0, "model_version": "stub-v0"}
    channels = {"console": ConsoleAlertChannel(), "broken": FailingChannel()}

    decision = evaluate_and_dispatch(prediction, policy, channels, db_path, now=0)

    assert decision.should_send is True  # dispatcher itself didn't crash
    with get_connection(db_path) as conn:
        rows = dict(conn.execute("SELECT channel, status FROM alerts_sent").fetchall())
    assert rows == {"console": "sent", "broken": "failed"}
    
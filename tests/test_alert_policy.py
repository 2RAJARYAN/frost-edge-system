import pytest

from alerts.alert_policy import AlertPolicy


@pytest.fixture
def policy():
    return AlertPolicy(risk_threshold=0.6, hysteresis_margin=0.1, cooldown_minutes=30)


def test_no_alert_below_threshold(policy):
    assert policy.evaluate(0.3, now=0).should_send is False


def test_alert_fires_on_crossing_threshold(policy):
    decision = policy.evaluate(0.65, now=0)
    assert decision.should_send is True
    assert "threshold" in decision.reason


def test_no_repeat_alert_immediately_after_first(policy):
    policy.evaluate(0.65, now=0)
    decision = policy.evaluate(0.66, now=10)
    assert decision.should_send is False


def test_hovering_at_threshold_does_not_spam(policy):
    """The exact failure mode the brief calls out."""
    policy.evaluate(0.61, now=0)
    d1 = policy.evaluate(0.59, now=5)
    d2 = policy.evaluate(0.61, now=10)
    d3 = policy.evaluate(0.58, now=15)
    assert d1.should_send is False
    assert d2.should_send is False
    assert d3.should_send is False


def test_reminder_fires_after_cooldown_elapses_while_still_above_threshold(policy):
    policy.evaluate(0.7, now=0)
    decision = policy.evaluate(0.7, now=1800)
    assert decision.should_send is True
    assert "reminder" in decision.reason


def test_clears_when_dropping_below_clear_threshold(policy):
    policy.evaluate(0.7, now=0)
    decision = policy.evaluate(0.4, now=10)
    assert decision.should_send is False
    assert "clear" in decision.reason


def test_can_re_alert_after_clearing_and_crossing_again(policy):
    policy.evaluate(0.7, now=0)
    policy.evaluate(0.4, now=10)
    decision = policy.evaluate(0.65, now=20)
    assert decision.should_send is True
    assert "crossed" in decision.reason


def test_invalid_hysteresis_margin_rejected():
    with pytest.raises(ValueError):
        AlertPolicy(risk_threshold=0.6, hysteresis_margin=-0.1, cooldown_minutes=30)

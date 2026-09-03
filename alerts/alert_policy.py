import time
from dataclasses import dataclass


@dataclass
class AlertDecision:
    should_send: bool
    reason: str


class AlertPolicy:
    """Decides *whether* to alert -- separate from *how* (that's
    AlertChannel's job; Single Responsibility, §8.2).

    Two independent mechanisms:

    Hysteresis -- entering alert state needs risk_score >=
    risk_threshold, but *clearing* it needs dropping below a lower
    clear_threshold. That gap is what stops a score hovering right at
    the line from flapping in and out every tick.

    Cooldown -- even during one sustained event, don't resend more
    than once per cooldown_minutes. A frost night could stay above
    threshold for hours; this turns that into periodic reminders
    instead of one message per prediction tick.
    """

    def __init__(
        self,
        risk_threshold: float,
        hysteresis_margin: float,
        cooldown_minutes: float,
    ):
        if hysteresis_margin < 0:
            raise ValueError("hysteresis_margin must be >= 0")
        self.risk_threshold = risk_threshold
        self.clear_threshold = risk_threshold - hysteresis_margin
        self.cooldown_seconds = cooldown_minutes * 60

        self._alerting = False
        self._last_alert_time: float | None = None

    def evaluate(self, risk_score: float, now: float | None = None) -> AlertDecision:
        """Call once per new prediction. `now` (epoch seconds) is
        injectable purely so tests can control time deterministically
        instead of sleeping or mocking the clock."""
        now = now if now is not None else time.time()

        if not self._alerting:
            if risk_score >= self.risk_threshold:
                self._alerting = True
                self._last_alert_time = now
                return AlertDecision(True, "risk crossed above threshold")
            return AlertDecision(False, "below threshold")

        if risk_score < self.clear_threshold:
            self._alerting = False
            self._last_alert_time = None
            return AlertDecision(False, "risk dropped below clear threshold")

        elapsed = now - self._last_alert_time
        if elapsed >= self.cooldown_seconds:
            self._last_alert_time = now
            return AlertDecision(
                True, "reminder: still above threshold, cooldown elapsed"
            )

        return AlertDecision(
            False, f"cooldown active ({elapsed:.0f}s / {self.cooldown_seconds:.0f}s)"
        )

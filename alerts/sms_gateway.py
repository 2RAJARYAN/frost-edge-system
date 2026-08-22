"""
Owner: TBD -- SMS gateway integration goes here.

Contract (see alerts/base.py):

    __init__(self, api_key: str, api_url: str, to_number: str)
        From config.yaml's `sms:` section.

    send(self, message: str) -> None
        REST call to your chosen transactional SMS provider (see
        Feasibility Study §2.3 -- confirm current free-tier pricing
        before committing). Raise AlertSendError on failure.

Inbound/"answering" SMS is explicitly Phase 4+ stretch goal per the
brief -- don't build it into this class.
"""

from alerts.base import AlertChannel, AlertSendError


class SmsAlertChannel(AlertChannel):
    def __init__(self, api_key: str, api_url: str, to_number: str):
        self.api_key = api_key
        self.api_url = api_url
        self.to_number = to_number

    def send(self, message: str) -> None:
        raise NotImplementedError(
            "SmsAlertChannel.send() not implemented yet -- "
            "see module docstring for the contract to build against."
        )

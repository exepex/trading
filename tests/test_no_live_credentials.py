"""The test run never holds a live credential, so no test can post to #fno-desk or reach a real service."""

import os

from fno.composition import build_alert_sender
from tests.live_credentials import LIVE_CREDENTIALS


def test_no_live_credential_is_visible_to_a_test():
    assert not [name for name in LIVE_CREDENTIALS if name in os.environ]


def test_the_real_alert_wiring_sends_nothing_in_tests():
    assert build_alert_sender().send("test") == "alert NOT sent: FNO_SLACK_BOT_TOKEN is not set"

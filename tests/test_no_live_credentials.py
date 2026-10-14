"""The test run never holds a live credential, so no test can post to #fno-desk or reach a real service."""

import os
from pathlib import Path

from fno import constants
from fno.alerts.sender import NoAlertSender
from fno.composition import build_alert_sender
from fno.env_file import ENV_FILE_NAME
from tests.live_credentials import LIVE_CREDENTIALS, NOT_CREDENTIALS


def test_every_environment_name_is_classed_as_credential_or_not():
    """Not circular: the names come from fno/constants.py, so dropping one from the guard's list fails here."""
    names = {getattr(constants, n) for n in dir(constants) if n.startswith("ENV_")}
    assert names == set(LIVE_CREDENTIALS) | set(NOT_CREDENTIALS)
    assert not set(LIVE_CREDENTIALS) & set(NOT_CREDENTIALS)


def test_no_live_credential_is_visible_to_a_test():
    assert not [name for name in LIVE_CREDENTIALS if name in os.environ]


def test_the_real_alert_wiring_is_the_silent_one_in_tests():
    assert isinstance(build_alert_sender(), NoAlertSender)  # checked without sending anything


def test_the_machine_env_file_is_out_of_reach(empty_home):
    """`python -m fno` loads ~/.trading.env; in tests home is an empty folder, so nothing is reloaded."""
    assert Path.home() == empty_home and not (empty_home / ENV_FILE_NAME).exists()

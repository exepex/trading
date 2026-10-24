"""Story O11: the recorded day replayed once per test (`day`: the outputs, the repository root and the alerts sent)."""

import pytest

from tests.desk.conftest import RecordingAlerts

from .replay import Replay


@pytest.fixture
def day(tmp_path, monkeypatch):
    alerts = RecordingAlerts()
    return Replay(tmp_path, monkeypatch, alerts).run(), tmp_path, alerts

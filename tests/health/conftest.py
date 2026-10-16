"""Every health test runs with a trial report that writes nothing: the real one appends to the repository's
`research/ops/trial_days.csv` (story O10), which a test must never touch. `test_trial.py` builds its own."""

import pytest


class NoTrial:
    def lines(self, run):
        return []

    def record(self):
        pass


@pytest.fixture(autouse=True)
def no_real_trial(monkeypatch):
    monkeypatch.setattr("fno.health.wiring.build_trial_report", lambda: NoTrial())

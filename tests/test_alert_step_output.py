"""Stories O8b and O8c (judges 240 and 246): the step-output sender records `posted=true` only when Slack accepted the
line, so a workflow's own failure line speaks exactly when the step did not."""

import pytest

from fno.alerts.sender import SENT, AlertSender
from fno.alerts.step_output import POSTED, StepOutputAlerts


class Inner(AlertSender):
    def __init__(self, outcome):
        self.outcome, self.sent = outcome, []

    def send(self, text):
        self.sent.append(text)
        return self.outcome


@pytest.mark.parametrize(("outcome", "posted"), [(SENT, True), ("alert NOT sent: no token", False)])
def test_posted_is_recorded_only_for_an_accepted_line(tmp_path, outcome, posted):
    outputs = tmp_path / "out"
    inner = Inner(outcome)
    assert StepOutputAlerts(inner, {"GITHUB_OUTPUT": str(outputs)}).send("one line") == outcome
    assert inner.sent == ["one line"] and (outputs.is_file() and outputs.read_text() == POSTED) is posted


def test_outside_actions_nothing_is_recorded(tmp_path):
    assert StepOutputAlerts(Inner(SENT), {}).send("x") == SENT and list(tmp_path.iterdir()) == []

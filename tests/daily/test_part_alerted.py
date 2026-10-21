"""Story O1 fix (judge 412 add. 1 note 2, after A4's 1f005e5a): a 3 pm part that alerted for itself gets no second
alert, Slack up or down. Its unsent alert is kept out of the committed lines (A4), so whether it alerted is read from
its whole output, through the real `ChildProcess`."""

import subprocess
import sys
import tempfile
from datetime import date, datetime

import pytest

from fno.alerts.sender import SENT
from fno.daily.processes import UNSENT, ChildProcess, Processes
from fno.daily.quote_parts import QUOTE_PARTS, QuoteParts
from fno.models import IST
from tests.timetable.fakes import Clock

from .fakes import RecordingCommitter

DAY = date(2026, 10, 14)
UNSENT_LINE = f"{UNSENT}: ConnectionError | 3 pm quote recorder: raw quote file NOT saved to Drive (folder FOLDERID42)"


class Alerts:
    def __init__(self):
        self.sent = []

    def send(self, text):
        self.sent.append(text)
        return SENT


class RealChildren(Processes):
    """Each part is a real child process that prints `printed` and exits 1, read by the real `ChildProcess`."""

    def __init__(self, printed: list[str], relayed: list[str]):
        self.printed, self.relayed = printed, relayed

    def start(self, arguments):
        output = tempfile.TemporaryFile("w+", encoding="utf-8")  # noqa: SIM115 - closed by ChildProcess once read
        script = "import sys; print(sys.argv[1]); raise SystemExit(1)"
        popen = subprocess.Popen([sys.executable, "-c", script, "\n".join(self.printed)], stdout=output,
                                 stderr=subprocess.STDOUT, text=True, start_new_session=True)  # fmt: skip
        popen.wait()
        return ChildProcess(popen, output, self.relayed.append)


@pytest.mark.parametrize(
    "printed, own_alert",
    [
        (["window closed: - (0 contracts, complete=False)", UNSENT_LINE], True),  # Slack down: unsent, still its own
        (["window closed: - (0 contracts, complete=False)", SENT], True),  # Slack up
        (["window closed: - (0 contracts, complete=False)"], False),  # it never alerted: O1 alerts once
    ],
    ids=["own-alert-unsent", "own-alert-sent", "silent"],
)
def test_a_failed_part_is_alerted_exactly_once_and_its_unsent_text_never_reaches_the_kept_lines(printed, own_alert):
    clock = Clock()
    clock.now = datetime(2026, 10, 14, 14, 56, tzinfo=IST)
    relayed, alerts = [], Alerts()
    nifty = (QUOTE_PARTS[0],)
    parts = QuoteParts(nifty, RealChildren(printed, relayed), RecordingCommitter(clock, []), lambda specs: [], alerts,
                       clock)  # fmt: skip
    parts.start(DAY)
    parts.service()
    assert parts.results["nifty"]["status"] == "failed"
    assert len(alerts.sent) == (0 if own_alert else 1)  # O1's PART_NOT_OK only for the silent part
    assert relayed == [line for line in printed if UNSENT in line]  # the unsent alert reaches the routine once
    assert all("FOLDERID42" not in line for line in parts.results["nifty"]["lines"])  # never in the run log

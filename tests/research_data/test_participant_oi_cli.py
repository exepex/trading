"""Story A8: `python -m fno participant-oi rule` and `watch` (the scheduled release-time recorder's entry point)."""

from datetime import datetime

import fno.composition
from fno.cli import main
from fno.constants import RELEASE_PRESENT, RELEASE_UNREACHABLE
from fno.models import IST
from fno.research_data.release_times import ReleaseCheck


def test_rule_prints_the_rule_in_force_and_the_measured_days(capsys):
    assert main(["participant-oi", "rule"]) == 0
    out = capsys.readouterr().out
    assert out.startswith("rule: ") and "of 20" in out


class FakeRecorder:
    def __init__(self, outcome, rechecked=()):
        self.outcome, self.calls, self.rechecked = outcome, [], list(rechecked)

    def recheck_recent(self, today):
        return self.rechecked

    def watch(self, day, until, every):
        self.calls.append((day, until, every))
        if self.outcome is None:
            return None
        return ReleaseCheck(day, datetime(2026, 10, 9, 19, 5, tzinfo=IST), self.outcome, "ab" * 32)


def test_watch_passes_the_day_cutoff_and_interval_and_fails_only_when_nse_was_unreachable(monkeypatch, capsys):
    for outcome, code in ((RELEASE_PRESENT, 0), (None, 0), (RELEASE_UNREACHABLE, 1)):
        recorder = FakeRecorder(outcome)
        monkeypatch.setattr(fno.composition, "build_release_time_recorder", lambda log=None, r=recorder: r)
        assert main(["participant-oi", "watch", "--day", "2026-10-09", "--until", "21:30", "--every", "10"]) == code
        day, until, every = recorder.calls[0]
        assert (str(day), until.isoformat(), every.total_seconds()) == ("2026-10-09", "2026-10-09T21:30:00+05:30", 600)
    assert "present at 2026-10-09 19:05 IST abababababab" in capsys.readouterr().out


def test_watch_reports_a_rewritten_file_and_fails_so_the_routine_notices(monkeypatch, capsys):
    rewritten = ReleaseCheck(
        datetime(2026, 10, 8).date(), datetime(2026, 10, 9, 18, 0, tzinfo=IST), "rewritten", "cd" * 32
    )
    recorder = FakeRecorder(RELEASE_PRESENT, [rewritten])
    monkeypatch.setattr(fno.composition, "build_release_time_recorder", lambda log=None: recorder)
    assert main(["participant-oi", "watch", "--day", "2026-10-09"]) == 1
    assert (
        "REWRITTEN 2026-10-08: NSE's file changed after it was first seen (now cdcdcdcdcdcd)" in capsys.readouterr().out
    )

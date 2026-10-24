"""Story G10 completion, criteria 4, 7 and 11: `v4-pack release` and `v4-pack deadline` print their lines, exit 1 only
when the run failed, commit the receipts only with `--commit` (the daily run commits them itself), and the deadline
posts the overlap watch's line to #fno-desk before its own lines (its last line is the step's reason)."""

import argparse
from datetime import date

import pytest

from fno.v4_pack import cli


class Run:
    def __init__(self, failed, lines, notes=()):
        self.failed, self.lines, self.notes = failed, lines, list(notes)

    def run(self, today):
        return self.lines


class Committer:
    def __init__(self):
        self.messages = []

    def commit(self, message):
        self.messages.append(message)
        return "receipts committed"


class Alerts:
    def __init__(self):
        self.sent = []

    def send(self, text):
        self.sent.append(text)
        return "alert sent"


@pytest.fixture
def seams(monkeypatch):
    committer, alerts, state = Committer(), Alerts(), {"overlap": None, "failed": False}
    monkeypatch.setattr("fno.config.load_config", lambda: {})
    monkeypatch.setattr("fno.models.now_ist", lambda: __import__("datetime").datetime(2026, 10, 26, 15, 15))
    monkeypatch.setattr("fno.storage.data_wiring.build_receipt_committer", lambda: committer)
    monkeypatch.setattr("fno.composition.build_alert_sender", lambda: alerts)
    released = ["v4 release 2026-10-26: A"]
    monkeypatch.setattr("fno.v4_pack.wiring.build_release_run",
                        lambda cfg: Run(state["failed"], released, state.get("notes", ())))  # fmt: skip
    monkeypatch.setattr("fno.v4_pack.wiring.build_deadline_run",
                        lambda cfg: Run(state["failed"], ["v4 deadline 2026-10-26: 4 on time, 0 late"]))  # fmt: skip

    class Watch:
        def line(self, today):
            assert today == date(2026, 10, 26)
            return state["overlap"]

    monkeypatch.setattr("fno.v4_pack.wiring.build_overlap_watch", lambda cfg: Watch())
    return committer, alerts, state


def call(command, commit=False):
    return cli.cmd_v4_pack(argparse.Namespace(v4_pack_cmd=command, commit=commit))


def test_a_good_release_exits_0_and_commits_nothing_without_the_flag(seams, capsys):
    committer, _, _ = seams
    assert call("release") == 0 and committer.messages == []
    assert capsys.readouterr().out.splitlines() == ["v4 release 2026-10-26: A"]


def test_by_hand_the_flag_commits_and_a_failed_run_exits_1(seams):
    committer, _, state = seams
    state["failed"] = True
    assert call("release", commit=True) == 1 and committer.messages == ["v4 release 2026-10-26"]


def test_the_deadline_posts_the_overlap_line_first_and_ends_on_its_own_line(seams, capsys):
    _, alerts, state = seams
    state["overlap"] = "v4 14:30 overlap 2026-10-26: v4 capture 2 failure(s) ..."
    assert call("deadline") == 0 and alerts.sent == [state["overlap"]]
    lines = capsys.readouterr().out.splitlines()
    assert lines[0] == state["overlap"] and lines[-1] == "v4 deadline 2026-10-26: 4 on time, 0 late"


def test_a_clean_overlap_posts_nothing(seams):
    _, alerts, _ = seams
    assert call("deadline") == 0 and alerts.sent == []


def test_a_v4_expiry_the_capture_could_not_choose_is_alerted_and_the_release_line_stays_last(seams, capsys):
    """Judge 581 m2: a day past the calendar's end records `v4_expiry: None`; the release alerts it, never silently."""
    _, alerts, state = seams
    state["notes"] = ["v4 release 2026-12-28: v4 expiry not chosen: ..."]
    assert call("release") == 0 and alerts.sent == state["notes"]
    assert capsys.readouterr().out.splitlines()[-1] == "v4 release 2026-10-26: A"

"""A22d end to end through `PreopenRecorder` (criteria D1, D5-D7): the 23 Oct shape gives a labelled value, the open
check runs only after the capture's commits and never moves GIFT's 08:40 read, and a check problem has its own line,
O10 row and alert, never a change to the capture."""

from __future__ import annotations

import threading
from datetime import date, timedelta

from fno.preopen.label_read import LabelRead

from .desk import Desk
from .fixtures import DAY, flat_0915, index_close, ist

D21, D20, D19, D16, D15 = (date(2026, 10, d) for d in (21, 20, 19, 16, 15))


class ReadAtOnce:
    """The label read run in the caller's thread: a test that needs the labels ready must not race a real thread."""

    def __init__(self, read):
        self.labels = read()

    def taken(self):
        return self.labels, []


def test_d1_the_23_oct_shape_gives_an_ok_value_labelled_unverified(tmp_path):
    desk = Desk(tmp_path, nifty=flat_0915(close=7777.25))
    assert desk.recorder(label_read=ReadAtOnce).record(DAY) == 0
    row = desk.day_row()
    nifty = (row["nifty_status"], row["nifty_preopen"], row["nifty_preopen_basis"])
    assert nifty == ("ok", "7777.25", "flat_0915_unverified")
    times = (row["nifty_source_time"], row["nifty_seen_at"], row["banknifty_preopen_basis"])
    assert times == ("", "09:10:00", "candle_0909")
    assert "nifty ok (1 read(s))" in desk.out and "7777.25" not in desk.committed_text()


def test_d6_five_matched_checks_label_todays_flat_value_verified(tmp_path):
    desk = Desk(tmp_path, nifty=flat_0915())
    for day in (D21, D20, D19, D16, D15):
        desk.official[day] = index_close()
        desk.plant_day_row(day, nifty="5555.5", banknifty="6666.5")
    desk.open_check().run(DAY)
    desk.recorder(label_read=ReadAtOnce).record(DAY)
    assert desk.day_row()["nifty_preopen_basis"] == "flat_0915_verified"


def test_d5_a_mismatch_has_its_own_alert_and_o10_row_and_leaves_the_capture_alone(tmp_path):
    desk = Desk(tmp_path, official={D21: index_close(nifty_open=5000.0)})
    desk.plant_day_row(D21, nifty="5555.5")
    assert desk.recorder(label_read=ReadAtOnce).record(DAY) == 1
    assert "pre-open recorded" in desk.out and desk.day_row()["nifty_status"] == "ok"
    line = "nifty open check mismatch: flat_0915_unverified value differs from NSE's official open on 2026-10-21"
    assert desk.sender.sent == [f"A22 open check 2026-10-22: {line}"]  # the capture had no problem: no alert of its own
    assert desk.out[-2] == f"open check with problems: {line}"
    assert [(e.step, e.kind) for e in desk.errors.rows()] == [("nifty open check", "mismatch")]
    assert not any(v in desk.sender.sent[0] for v in ("5555", "5000", "555.5"))


def test_d7_a_slow_store_never_moves_gifts_0840_read_and_the_check_follows_the_commits(tmp_path):
    desk = Desk(tmp_path, nifty=flat_0915(), official={D21: index_close(), D20: index_close()})
    desk.plant_day_row(D21, nifty="5555.5")
    desk.open_check().run(DAY)  # D21 now has a check file: the label read must read it
    desk.plant_day_row(D20, nifty="5555.5")  # unchecked: the open check reads it after the commits
    release, commits_before_check = threading.Event(), []

    def slow(path):
        if threading.current_thread() is threading.main_thread():
            commits_before_check.append(len(desk.committers[1].calls))
            desk.clock.at += timedelta(minutes=10)  # each check read takes 10 minutes
        else:
            release.wait(5)  # the label read is stuck in Drive for the whole capture

    desk.on_read = slow
    try:
        assert desk.recorder().record(DAY) == 1
    finally:
        release.set()
    assert desk.early.at == [ist(8, 40)]  # GIFT read and pushed at 08:40:00
    assert commits_before_check == [1]  # the capture's commit came first; the check read once (D20)
    row = desk.day_row()
    assert (row["nifty_status"], row["nifty_preopen_basis"]) == ("ok", "flat_0915_unverified")
    alert = desk.sender.sent[0]
    assert alert.startswith("A22 pre-open capture 2026-10-22: open check labels late: not read by the day row")
    assert [c.calls for c in desk.committers] == [["pre-open 2026-10-22"] * 2] * 2
    assert desk.out[-1] == "open check: 1 checked, 0 waiting for NSE's file"


def test_the_background_label_read_gives_its_labels_or_its_error_kind():
    done = LabelRead(lambda: {"nifty": "verified"})
    done._thread.join()
    assert done.taken() == ({"nifty": "verified"}, [])

    def broken():
        raise OSError("Drive down")

    failed = LabelRead(broken)
    failed._thread.join()
    labels, [problem] = failed.taken()
    assert labels == {} and problem.line() == "open check labels failed: OSError"

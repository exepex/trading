"""A16's mark observer port (LM1, the position monitor, plugs in behind it): one call per newly settled mark with the
ledger's own status string, this run's document only for the mark it took, and an observer failure never stops the
recorder."""

from datetime import time

from fno.intraday.observer import MarkObserver, NoObserver
from fno.intraday.slots import label
from fno.intraday.status import MISSED
from tests.intraday.fakes import DAY, FakeClock, build, ist


class Recording(MarkObserver):
    def __init__(self):
        self.calls = []

    def after_mark(self, day, mark, document, status):
        self.calls.append((mark, status, document))


class Broken(MarkObserver):
    def after_mark(self, day, mark, document, status):
        raise ValueError("a message that must never be printed")


def test_every_settled_mark_reaches_the_observer_once_with_its_ledger_status(tmp_path):
    clock = FakeClock(ist(DAY, 10, 20))  # 09:15-10:15 have passed: settled as missed on the first snapshot
    recorder, *_ = build(tmp_path, clock)
    recorder.observer = observer = Recording()
    recorder.run(time(10, 35))
    seen = [(label(m), s) for m, s, _ in observer.calls]
    assert seen == [("09:15", MISSED), ("09:30", MISSED), ("09:45", MISSED), ("10:00", MISSED), ("10:15", MISSED),
                    ("10:30", "good")]  # fmt: skip
    rows = {r["mark_ist"]: r["status"] for r in recorder.ledger.rows(DAY)}
    assert all(rows[h] == s for h, s in seen)  # exactly the ledger's strings
    documents = {m: d for m, _, d in observer.calls}
    assert documents[ist(DAY, 10, 30)].mark == ist(DAY, 10, 30)  # this run's own snapshot, from memory
    assert all(d is None for m, d in documents.items() if m != ist(DAY, 10, 30))


def test_a_failing_observer_never_stops_the_rows_or_the_commit(tmp_path):
    recorder, _, _, publisher, _ = build(tmp_path, FakeClock(ist(DAY, 10, 25)))
    recorder.observer = Broken()
    outcomes = recorder.run(time(10, 35))
    lines = [line for o in outcomes for line in o.lines]
    assert any(line.startswith("mark observer failed at 10:30: ValueError") for line in lines)
    assert not any("must never be printed" in line for line in lines)
    assert {r["mark_ist"]: r["status"] for r in recorder.ledger.rows(DAY)}["10:30"] == "good"
    assert publisher.commits  # the run still committed its files


def test_the_live_wiring_starts_with_no_observer(tmp_path, monkeypatch):
    from fno.intraday import wiring
    from tests.intraday.groww_fakes import FakeGrowwProvider

    monkeypatch.setattr(wiring, "GrowwProvider", lambda cfg: FakeGrowwProvider())
    assert isinstance(wiring.build_intraday_recorder({}, tmp_path).observer, NoObserver)

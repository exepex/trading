"""A run that starts after 15:13 IST (GitHub's schedule was 5 h late on 14 Oct) fires no AI book: its answer could
only be late, and the collection, seconds later, could only record nothing. Both books are recorded `not_fired`
with the reason "late start" (no session exists to open), and #fno-desk gets one line."""

import json

from fno.ai.collect import AiForecastCollector
from fno.ai.fire import AiBookFirer
from fno.ai.history import RepoHistory
from fno.ai.paths import fired_path
from fno.ai.record_writer import AiRecordWriter
from fno.constants import BOOK2_HYBRID, BOOK3_AI
from tests.ai.fakes import DAY, Clock, at
from tests.ai.test_fire_and_collect import Desk


def fire_at(desk, hour, minute, second=0):
    return AiBookFirer(desk.root, desk.triggers, desk.alerts, Clock(at(hour, minute, second))).fire(DAY)


def test_a_run_starting_after_1513_fires_no_book_and_says_so_once(tmp_path):
    desk = Desk(tmp_path)
    assert fire_at(desk, 19, 27)[0].endswith("fired none of book2_hybrid, book3_ai")
    assert all(t.fired == [] for t in desk.triggers.values())
    log = json.loads((desk.root / fired_path(DAY)).read_text())
    assert all(not log[b]["fired"] and log[b]["late_start"] for b in (BOOK2_HYBRID, BOOK3_AI))
    assert len(desk.alerts.lines) == 1 and "late start" in desk.alerts.lines[0]


def test_a_late_start_is_recorded_not_fired_with_its_reason(tmp_path):
    desk = Desk(tmp_path)
    fire_at(desk, 19, 27)
    AiForecastCollector(desk.root, RepoHistory(desk.root), desk.receipts, AiRecordWriter(desk.root),
                        Clock(at(19, 28))).collect(DAY)  # fmt: skip
    for book in (BOOK2_HYBRID, BOOK3_AI):
        audit = desk.audit(book)
        assert audit["status"] == "not_fired" and any("late start" in n for n in audit["notes"])
        assert all(r.record.probability is None for r in desk.records(book).values())


def test_a_run_starting_at_1513_still_fires(tmp_path):
    desk = Desk(tmp_path)
    fire_at(desk, 15, 13, 0)
    assert all(len(t.fired) == 1 for t in desk.triggers.values()) and desk.alerts.lines == []

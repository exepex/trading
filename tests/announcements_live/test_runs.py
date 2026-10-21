"""First-seen across runs and the cutoff (story A21 part 2, criteria 8, 9 and 12)."""

from fno.announcements_live.reading import items_as_of

from .helpers import DAY, Clock, Source, at, item, poller


def test_a_second_run_keeps_the_first_runs_times_and_adds_only_new_items(tmp_path):
    clock = Clock(at("11:00"))
    first, _, _ = poller(tmp_path, Source(clock, [item("1"), item("2")]), clock, "20261019T053000Z-aaaaaa")
    first.after_mark(DAY, at("11:00"), None, "good")
    clock2 = Clock(at("11:15"))
    second, failures, _ = poller(tmp_path, Source(clock2, [item("1"), item("2"), item("3")]), clock2,
                                 "20261019T054500Z-bbbbbb")  # fmt: skip
    second.after_mark(DAY, at("11:15"), None, "good")
    state = second.days.load(DAY)  # read back as a third run would
    times = {row["seq_id"]: row["first_seen_at"][11:19] for row in state.items}
    assert times == {"1": "11:00:02", "2": "11:00:02", "3": "11:15:02"} and failures.rows == []  # arrivals


def test_an_unreadable_seen_set_stops_the_run_loudly_and_polls_nothing(tmp_path):
    class Broken:
        def load(self, day):
            raise RuntimeError("Drive down")

    clock = Clock(at("11:00"))
    source = Source(clock, [item("1")])
    run, failures, alerts = poller(tmp_path, source, clock, "20261019T053000Z-cccccc", days=Broken())
    run.after_mark(DAY, at("11:00"), None, "good")
    run.after_mark(DAY, at("11:15"), None, "good")
    assert source.calls == 0 and failures.kinds() == ["seen_set_unreadable"] and len(alerts.sent) == 1


def test_the_cutoff_uses_first_seen_never_nses_time():
    rows = [
        {"seq_id": "1", "first_seen_at": at("14:30").isoformat(), "exchdisstime": "19-Oct-2026 09:00:00"},
        {"seq_id": "2", "first_seen_at": at("14:30", 1).isoformat(), "exchdisstime": "19-Oct-2026 09:00:00"},
    ]
    assert [r["seq_id"] for r in items_as_of(rows, at("14:30"))] == ["1"]  # at the cutoff kept, 1 s after dropped
    assert items_as_of([], at("14:30")) == []


def test_a_closed_day_makes_no_request(tmp_path):
    clock = Clock(at("11:00"))
    source = Source(clock, [item("1")])
    run, failures, _ = poller(tmp_path, source, clock, "20261019T053000Z-dddddd", session=False)
    run.after_mark(DAY, at("11:00"), None, "good")
    assert source.calls == 0 and failures.rows == []

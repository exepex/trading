"""The owner's "5 A": a routine records its own usage at the end of each run, as its own timing of the run."""

import json
from datetime import date

import pytest

from fno.budget.self_timed import SOURCE, SelfTimedUsageReader
from fno.budget.usage_ledger import Attribution, UsageLedger
from fno.budget.usage_reader import ExportRefused

RUN = {"session_id": "session_01BOOKxyz", "model": "m", "started_at": "2026-10-16T09:40:00Z",
       "ended_at": "2026-10-16T09:52:30Z"}  # fmt: skip


def reader(tmp_path, **changes):
    path = tmp_path / "run.json"
    path.write_text(json.dumps(RUN | changes), encoding="utf-8")
    return SelfTimedUsageReader(path)


def test_a_run_gives_its_wall_minutes_on_its_ist_day_with_unknown_tokens(tmp_path):
    (day,) = reader(tmp_path).days()
    assert (day.day, day.minutes, day.turns, day.tokens, day.source) == (date(2026, 10, 16), 12.5, 1, None, SOURCE)
    assert day.captured_at == "2026-10-16T15:22:30+05:30"


def test_the_finished_run_is_recorded_the_same_day(tmp_path):
    usage = reader(tmp_path)
    lines = UsageLedger(tmp_path).record(usage.days(), Attribution("books_and_roles", "book2_hybrid"),
                                         usage.complete_before(date(2026, 10, 16)))  # fmt: skip
    (row,) = UsageLedger(tmp_path).rows()
    assert "recorded 12.5 minutes" in lines[0] and row["tokens_basis"] == "not available" and row["source"] == SOURCE


def test_a_run_crossing_midnight_ist_counts_on_its_end_day(tmp_path):
    (day,) = reader(tmp_path, started_at="2026-10-16T18:20:00Z", ended_at="2026-10-16T18:40:00Z").days()
    assert day.day == date(2026, 10, 17) and day.minutes == 20.0


@pytest.mark.parametrize("changes, match", [({"ended_at": "2026-10-16T09:30:00Z"}, "before started_at"),
                                            ({"started_at": "2026-10-16T09:40:00"}, "no time zone"),
                                            ({"session_id": ""}, "no session_id")])  # fmt: skip
def test_a_bad_timing_record_is_refused(tmp_path, changes, match):
    with pytest.raises(ExportRefused, match=match):
        reader(tmp_path, **changes).days()

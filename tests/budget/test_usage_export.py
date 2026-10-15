"""Story F8 criteria 4 and 5: usage comes only from the session's own figures, per IST day, and an incomplete export is
refused."""

from datetime import date

import pytest

from fno.budget.usage_export import ExportFileUsageReader, ExportRefused
from tests.budget.exports import REPLY, SESSION_ID, TWO_DAYS, export, result_event, write_export


def days_of(tmp_path, data):
    return ExportFileUsageReader(write_export(tmp_path, data)).days()


def test_minutes_and_tokens_are_summed_per_ist_day(tmp_path):
    first, second = days_of(tmp_path, export(TWO_DAYS))
    assert (first.day, first.minutes, first.turns) == (date(2026, 10, 14), 1.0, 1)
    assert (second.day, second.minutes, second.turns) == (date(2026, 10, 15), 2.0, 2)
    assert second.tokens == {"input_tokens": 8, "output_tokens": 200, "cache_read_tokens": 2000,
                             "cache_write_tokens": 100}  # fmt: skip
    assert (first.session_id, first.model) == (SESSION_ID, "model-x")


def test_an_unwrapped_export_reads_the_same(tmp_path):
    assert days_of(tmp_path, export(TWO_DAYS, wrapped=False)) == days_of(tmp_path, export(TWO_DAYS))


def test_a_day_with_a_turn_without_usage_has_unknown_tokens_never_zero(tmp_path):
    events = [result_event("2026-10-14T05:00:00Z", 60_000, "u1"), result_event("2026-10-14T06:00:00Z", 60_000, "u2",
                                                                              output_tokens=None)]  # fmt: skip
    (day,) = days_of(tmp_path, export(events))
    assert day.tokens is None and day.minutes == 2.0


def test_an_export_missing_older_pages_is_refused(tmp_path):
    with pytest.raises(ExportRefused, match="older result events are missing"):
        days_of(tmp_path, export(TWO_DAYS, has_more=True))


def test_the_same_event_on_two_pages_counts_once(tmp_path):
    data = export(TWO_DAYS[:1])
    data["result_pages"].append(data["result_pages"][0])
    assert days_of(tmp_path, data)[0].minutes == 1.0


def test_a_turn_without_its_duration_is_refused_not_guessed(tmp_path):
    event = result_event("2026-10-14T05:00:00Z", 60_000, "u1")
    event["result"]["internal_anthropic_catchall"]["duration_ms"] = None
    with pytest.raises(ExportRefused, match="no duration_ms"):
        days_of(tmp_path, export([event]))


def test_no_reply_text_is_kept(tmp_path):
    assert REPLY not in repr(days_of(tmp_path, export(TWO_DAYS)))


def test_an_export_without_a_session_id_is_refused(tmp_path):
    data = export(TWO_DAYS)
    data["session"]["ccr"]["id"] = ""
    with pytest.raises(ExportRefused, match="no id"):
        days_of(tmp_path, data)


# The orchestrator's five finished turns of 15 Oct 2026 (IST), figures copied from its real result events
# (created_at, duration_ms, usage.output_tokens), read by the builder with list_events(kinds=["result"]).
REAL_TURNS = [("2026-10-15T00:28:21Z", 28400, 1487), ("2026-10-15T00:29:02Z", 8206, 349),
              ("2026-10-15T00:30:39Z", 52437, 3834), ("2026-10-15T00:35:08Z", 126572, 12990),
              ("2026-10-15T00:35:28Z", 19935, 1419)]  # fmt: skip


def test_the_real_orchestrator_turns_of_15_october(tmp_path):
    events = [result_event(at, ms, f"r{n}", tokens) for n, (at, ms, tokens) in enumerate(REAL_TURNS)]
    (day,) = days_of(tmp_path, export(events))
    assert (day.day, day.minutes, day.turns, day.tokens["output_tokens"]) == (date(2026, 10, 15), 3.93, 5, 20079)


def test_events_without_a_uuid_are_all_counted(tmp_path):
    events = [result_event("2026-10-14T05:00:00Z", 60_000, ""), result_event("2026-10-14T06:00:00Z", 60_000, "")]
    assert days_of(tmp_path, export(events))[0].turns == 2

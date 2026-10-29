"""Story A16-429-recovery (orchestrator go, 29 Oct 2026): the real GW1a guard (60 s pause after a 429) under the real
A16 source on one simulated timeline. 29 Oct 10:15 lost 112 of 220 quotes to `GrowwRateLimitPaused`: the retry pass ran
inside the pause. Now it waits the pause out, asks nothing inside it, never asks after the mark's 120 s quiet window and
never faster than 4 a second, and the mark's notes keep the first 429 (the retry used to overwrite its call)."""

from datetime import datetime, timedelta

import pytest

from fno.intraday.groww_source import FIRST_429, PER_SECOND, WINDOW_ENDED
from fno.providers.groww_quiet_windows import QUIET_SECONDS
from fno.providers.groww_rate_guard import PAUSE_SECONDS
from tests.intraday.groww_fakes import FakeGrowwApi
from tests.intraday.sim_429 import MARK, QUOTES, asked_times, lost, mark_with


def answered_429(doc) -> datetime:
    note = next(n for n in doc.notes if n.startswith("first_429"))
    return datetime.fromisoformat(note.split(" answered ")[1].split()[0])


def window_end() -> datetime:
    return MARK + timedelta(seconds=QUIET_SECONDS)


def test_a_429_after_91_quotes_loses_nothing_now_where_29_oct_lost_112_of_220():
    doc = mark_with({92})  # 29 Oct 10:15: about 130 quotes were refused in the first pass
    assert len(doc.quotes) == QUOTES and any(n.startswith("quotes_retried:") for n in doc.notes)
    assert lost(doc) == 0 and doc.recorded_contracts == doc.expected_contracts
    assert doc.sleeps and sum(doc.sleeps) <= PAUSE_SECONDS  # it waited out the pause, once, and no longer


def test_the_retry_asks_nothing_inside_the_pause_and_nothing_after_the_quiet_window():
    doc = mark_with({30}, chain_seconds=2.5)
    answered = answered_429(doc)
    assert [t for t in asked_times(doc) if answered < t < answered + timedelta(seconds=PAUSE_SECONDS)] == []
    assert max(asked_times(doc)) < window_end()
    assert not any(q.failure == "GrowwRateLimitPaused" for q in doc.quotes)


def test_a_429_on_the_first_quote_recovers_all_that_fits_and_names_the_rest_unasked():
    """Worst case: 5 s of chain calls, a 429 on the first quote, and 228 quotes at 4 a second: the quotes that cannot
    start before 120 s stay unasked and named."""
    doc = mark_with({1}, chain_seconds=2.5)
    resume = answered_429(doc) + timedelta(seconds=PAUSE_SECONDS)
    fits = int((window_end() - resume).total_seconds() * PER_SECOND)
    assert abs(lost(doc) - max(0, QUOTES - fits)) <= 2
    assert {q.failure for q in doc.quotes if q.failure} <= {WINDOW_ENDED}
    assert max(asked_times(doc)) < window_end()


def test_the_retry_never_goes_faster_than_4_a_second():
    times = asked_times(mark_with({30}))
    assert min((b - a).total_seconds() for a, b in zip(times, times[1:], strict=False)) >= 1 / PER_SECOND - 1e-6


def test_the_first_429_stays_in_the_notes_with_its_call_time_and_code():
    doc = mark_with({10, 11})
    notes = [n for n in doc.notes if n.startswith("first_429")]
    assert len(notes) == 1 and "quote NIFTY26" in notes[0] and notes[0].endswith("GrowwRateLimited:429")
    assert notes[0].startswith(FIRST_429.split("{")[0])


def test_a_late_429_whose_pause_outlasts_the_window_skips_the_retry_and_says_so():
    doc = mark_with({226}, chain_seconds=2.5)  # 61 s in: the pause would end at 121.5 s
    assert any(n.startswith("quotes_retry_skipped") for n in doc.notes)
    assert not any(n.startswith("quotes_retried") for n in doc.notes) and not doc.sleeps
    assert max(asked_times(doc)) < window_end()


def test_a_mark_without_a_429_is_unchanged():
    doc = mark_with(set())
    assert lost(doc) == 0 and not doc.sleeps and not any("429" in n or "retr" in n for n in doc.notes)


def test_a_failure_that_is_not_a_429_is_retried_at_once_without_waiting():
    doc = mark_with(set(), api=FakeGrowwApi(index_level=24000.0, fail=("NIFTY26101922600CE",)))
    assert "quotes_retried:1" in doc.notes and not doc.sleeps
    assert not any(n.startswith("first_429") for n in doc.notes)


@pytest.mark.parametrize("number", [5, 50, 150, 1])
def test_the_real_29_oct_shapes_all_end_inside_the_window(number):
    assert max(asked_times(mark_with({number}, chain_seconds=2.0))) < window_end()


def test_429s_of_calls_in_flight_together_name_the_first_and_wait_for_the_last_pause():
    """4 workers: calls sent before the first 429 returns meet the limit too, and each restarts the guard's pause. The
    note names the first answered; the retry starts after the last pause, never inside an earlier one."""
    doc = mark_with({40, 41, 42}, chain_seconds=2.0, in_flight=3)
    (first, first_at), (_, _), (_, last_at) = sorted(doc.api.answered_429, key=lambda a: a[1])
    assert last_at - first_at >= timedelta(seconds=1.0)
    notes = [n for n in doc.notes if n.startswith("first_429")]
    assert len(notes) == 1 and f"quote {first}" in notes[0]  # the first answered, not the last
    assert answered_429(doc) == first_at
    last_pause_ends = last_at + timedelta(seconds=PAUSE_SECONDS)
    assert [t for t in asked_times(doc) if first_at < t < last_pause_ends] == []  # nothing inside either pause
    assert not any(q.failure == "GrowwRateLimitPaused" for q in doc.quotes)  # so the retry was not refused
    retried = int(next(n for n in doc.notes if n.startswith("quotes_retried")).split(":")[1])
    fits = int((window_end() - last_pause_ends).total_seconds() * PER_SECOND)
    assert abs(lost(doc) - max(0, retried - fits)) <= 3  # what the window allows after the LAST pause, no more
    assert max(asked_times(doc)) < window_end()


def test_a_429_inside_the_retry_pass_keeps_the_first_in_the_notes_and_refuses_the_rest():
    """Judge 694 should-fix 1: the note is the mark's FIRST 429. A second one, in the retry pass (slot numbers after
    the first pass's 228), restarts the pause (nothing more is recovered: the pass is not repeated) but never replaces
    the note."""
    clean = mark_with({40})
    both = mark_with({40, 260})
    (first, first_at), (second, second_at) = sorted(both.api.answered_429, key=lambda a: a[1])
    assert second_at > first_at + timedelta(seconds=PAUSE_SECONDS)  # the second one came in the retry pass
    notes = [n for n in both.notes if n.startswith("first_429")]
    assert len(notes) == 1 and f"quote {first}" in notes[0] and f"quote {second}" not in notes[0]
    assert answered_429(both) == first_at
    assert lost(clean) == 0 and lost(both) > 0  # the second 429 cost the quotes behind it
    assert max(asked_times(both)) < window_end()


@pytest.mark.parametrize("chain_seconds", [0.0, 1.0, 2.0, 3.0])
def test_the_loss_is_set_by_when_the_first_pass_ends_wherever_the_429_falls(chain_seconds):
    """Judge 694 should-fix 2. The quotes after a 429 are paced even when refused, so the first pass always ends at F =
    the chain calls + quotes at 4 a second. The pause ends at (429 + 60.5 s) and the retries need (F - 429) more, so the
    retry ends at F + 60.5 s whatever the 429's moment: lost = 4 * (F + 60.5 - 120) quotes when that is positive. 27-29
    Oct's good marks: F median 59.75 s, so about one quote; see docs/stories/A16-429-recovery.md."""
    results = {}
    for where in (10, 60, 120):
        doc = mark_with({where}, chain_seconds=chain_seconds)
        pause_end = (answered_429(doc) - MARK).total_seconds() + PAUSE_SECONDS + 0.5
        first_pass_end = pause_end - sum(doc.sleeps)  # the retry slept from there to the end of the pause
        expected = max(0, round(PER_SECOND * (first_pass_end + PAUSE_SECONDS + 0.5 - QUIET_SECONDS)))
        results[where] = (lost(doc), expected, doc.sleeps, [n[:60] for n in doc.notes])
    assert all(abs(got - expected) <= 1 for got, expected, *_ in results.values()), results
    losses = [got for got, *_ in results.values()]
    assert max(losses) - min(losses) <= 1, results  # wherever the 429 falls

"""Story G11, the composition root and the CLI around the v4 run, pinned where the self-review of dfb26381 found
mutations that survived: both v2 steps stop on the books' v4 date, the v4 collector goes live on it, the stop rule's
window is 20 regular sessions, v4's weeks get audit seeds and audits, a v4 run without timing is named not captured,
and the cost report keeps 0 reveal calls as 0."""

import json
from datetime import date

import pytest

from fno.ai import wiring
from fno.ai.collect import AiForecastCollector
from fno.ai.run_terms import V4_TERMS
from fno.ai.usage_gaps import usage_gaps
from fno.ai.v4_cost import V4CostReport
from fno.constants import BOOK2_HYBRID, BOOK3_AI
from tests.ai.test_v4_cost import Ledger, timing

LIVE = date(2026, 11, 2)


@pytest.fixture
def live(monkeypatch):
    monkeypatch.setattr(wiring, "v4_live_from", lambda cfg=None: LIVE)
    return LIVE


def test_the_v2_fire_and_collect_and_the_v4_collect_all_take_the_books_v4_date(live):
    assert wiring.build_ai_firer({}).v4_live_from == live
    assert wiring.build_ai_collector({}).v4_live_from == live
    assert wiring.build_v4_collector({}).live_from == live


def test_the_v2_collection_records_nothing_from_the_v4_date(tmp_path):
    """Review of dfb26381: after go-live the v2 collect wrote no_submission for both books every day."""
    collector = AiForecastCollector(tmp_path, None, None, None, lambda: None, LIVE)
    [line] = collector.collect(LIVE)
    assert "v2 AI collection stopped: the books answer protocol v4 from 2026-11-02" in line
    assert not any(tmp_path.iterdir())


def test_the_stop_rules_window_is_twenty_regular_sessions():
    days = wiring.v4_sessions_before(date(2026, 10, 26))
    assert len(days) == 20 and days[-1] == date(2026, 10, 23) and date(2026, 10, 20) not in days  # 20 Oct: a holiday


def fire_log(root, day, books=(BOOK2_HYBRID, BOOK3_AI), session="https://claude.ai/code/cse_01AbC"):
    path = root / V4_TERMS.fired_path(day)
    path.parent.mkdir(parents=True, exist_ok=True)
    entries = {b: {"fired": True, "version": "x", "session": f"{session}{b}"} for b in books}
    path.write_text(json.dumps({"released": True, "books": entries}))


def test_v4s_weeks_get_audit_seeds(tmp_path, monkeypatch):
    for n in range(12):  # 12 fired v4 days: the last two are past the first 10 and need a weekly draw
        fire_log(tmp_path, date(2026, 11, 2 + n if n < 5 else 4 + n))
    asked = {}
    monkeypatch.setattr(wiring, "verified_seeds", lambda file, archive, weeks: asked.setdefault("weeks", weeks))
    monkeypatch.setattr(wiring.storage, "build_owner_drive", lambda env: None)
    wiring.build_audit_seeds(tmp_path, {})
    assert asked["weeks"] == {(2026, 46)}  # 14-15 Nov, after the first 10 fired days


def test_audits_due_lists_v4s_runs_apart(tmp_path, monkeypatch, capsys):
    from fno import cli

    fire_log(tmp_path, LIVE)
    monkeypatch.setattr("fno.config.ROOT", tmp_path)
    monkeypatch.setattr(wiring, "build_audit_seeds", lambda root=None, env=None: ({}, []))
    assert cli.main(["ai", "audits-due"]) == 0
    out = capsys.readouterr().out
    assert "audits due (v2): 0" in out and "audits due (v4): 2" in out and "2026-11-02 book3_ai" in out


def test_a_v4_run_that_published_no_timing_is_named_not_captured(tmp_path):
    """Review of dfb26381: BG1's capture coverage and F8c's alert read v4's fire logs too."""
    fire_log(tmp_path, LIVE, books=(BOOK3_AI,))
    gaps = usage_gaps(tmp_path, Ledger([]), LIVE)
    assert gaps == [("2026-11-02", BOOK3_AI)]
    captured = Ledger([{"session_id": "session_01AbCbook3_ai", "date": "2026-11-02", "book": BOOK3_AI}])
    assert usage_gaps(tmp_path, captured, LIVE) == []


def test_zero_reveal_calls_count_as_zero_never_as_unknown(tmp_path):
    rows = [timing(tmp_path, LIVE, BOOK3_AI, 5, 0.1, 0)]
    assert "reveal calls p50 0.00, p95 0.00" in V4CostReport(tmp_path, Ledger(rows), LIVE).lines()[1]


def test_a_v4_fire_log_that_is_not_an_object_is_named_unreadable(tmp_path):
    from fno.budget.capture_coverage import FireLogUnreadable, fired_sessions

    path = tmp_path / V4_TERMS.fired_path(LIVE)
    path.parent.mkdir(parents=True)
    path.write_text("[1, 2]")
    with pytest.raises(FireLogUnreadable):
        fired_sessions(tmp_path, "2026-11", "2026-12-01")


def test_the_firer_counts_misses_before_go_live_with_v4s_own_sessions():
    """Judge 586 F1: the daily count reads the calendar's v4 sessions, never the default empty list."""
    assert wiring.build_v4_firer({}).sessions_between is wiring.v4_sessions_between

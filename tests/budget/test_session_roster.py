"""Judge 104 must-fix 3: the development sessions of the month and whether each one's usage is fully captured."""

import json
from datetime import date

import pytest

from fno.budget.session_roster import ROSTER_FILE, SessionRoster, development_coverage, read_roster_export
from fno.budget.usage_reader import ExportRefused


def session(n, created="2026-10-14T03:00:00Z", updated="2026-10-14T06:00:00Z"):
    return {"id": f"session_0{n}", "title": "a title that is never kept", "created_at": created, "updated_at": updated}


def roster_export(tmp_path, pages, limit=2, captured="2026-10-16T08:00:00+05:30"):
    chained, cursor = [], None
    for sessions in pages:
        last = sessions[-1]["id"] if sessions else None
        chained.append({"after_id": cursor, "response": {"ccr": {"data": sessions, "first_id": "f", "last_id": last}}})
        cursor = last
    path = tmp_path / "roster.json"
    path.write_text(json.dumps({"captured_at": captured, "limit": limit, "pages": chained}), encoding="utf-8")
    return path


def test_a_chained_roster_is_read_to_its_end_and_keeps_no_titles(tmp_path):
    rows = read_roster_export(roster_export(tmp_path, [[session(1), session(2)], [session(3)]]))
    assert [r["session_id"] for r in rows] == ["session_01", "session_02", "session_03"]
    expected = {"session_id": "session_01", "created_at": "2026-10-14T08:30:00+05:30",
                "updated_at": "2026-10-14T11:30:00+05:30", "captured_at": "2026-10-16T08:00:00+05:30"}  # fmt: skip
    assert rows[0] == expected


def test_a_roster_that_may_continue_or_misses_a_page_is_refused(tmp_path):
    with pytest.raises(ExportRefused, match="last page is full"):
        read_roster_export(roster_export(tmp_path, [[session(1), session(2)]]))
    path = roster_export(tmp_path, [[session(1), session(2)], [session(3), session(4)], [session(5)]])
    data = json.loads(path.read_text(encoding="utf-8"))
    del data["pages"][1]
    path.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(ExportRefused, match="page 2 was not read with the previous page's last_id"):
        read_roster_export(path)


def test_merging_keeps_each_sessions_latest_activity(tmp_path):
    roster = SessionRoster(tmp_path)
    roster.record(read_roster_export(roster_export(tmp_path, [[session(1)]])))
    later = session(1, updated="2026-10-15T06:00:00Z")
    assert roster.record(read_roster_export(roster_export(tmp_path, [[later, session(2)]], limit=3))) == 2
    assert [r["updated_at"] for r in roster.rows()] == ["2026-10-15T11:30:00+05:30", "2026-10-14T11:30:00+05:30"]
    assert "title" not in (tmp_path / ROSTER_FILE).read_text(encoding="utf-8")


def usage(session_id, captured):
    return {"session_id": session_id, "captured_at": captured}


ROSTER = [{"session_id": "session_01", "created_at": "2026-10-14T08:30:00+05:30",
           "updated_at": "2026-10-15T11:30:00+05:30", "captured_at": "2026-10-16T08:00:00+05:30"}]  # fmt: skip


def test_a_session_is_covered_only_by_a_reading_taken_after_its_last_activity():
    before = date(2026, 10, 16)
    assert development_coverage(ROSTER, [usage("session_01", "2026-10-15T12:00:00+05:30")], "2026-10", before).complete
    stale = development_coverage(ROSTER, [usage("session_01", "2026-10-15T09:00:00+05:30")], "2026-10", before)
    assert not stale.complete and stale.missing == ("session_01",) and "1 development session(s)" in stale.reason
    assert not development_coverage(ROSTER, [], "2026-10", before).complete


def test_a_roster_read_before_the_last_complete_day_ended_is_stale():
    coverage = development_coverage(ROSTER, [usage("session_01", "2026-10-17T09:00:00+05:30")], "2026-10",
                                    date(2026, 10, 17))  # fmt: skip
    assert not coverage.complete and coverage.reason == "no session roster read since 2026-10-17T00:00:00+05:30"
    assert not development_coverage([], [], "2026-10", date(2026, 10, 16)).complete


def test_sessions_outside_the_month_do_not_count():
    assert development_coverage(ROSTER, [], "2026-09", date(2026, 10, 16)).complete  # roster read after September

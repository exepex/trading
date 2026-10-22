"""Story BG1 criteria 1, 3 and 7 end to end: the meter built from a repository's files, with the allocation apart from
cash spend, the cap basis and its limits, and missing captures of fired AI book sessions."""

import json
import subprocess
from datetime import date

import pytest

from fno.budget.capture_coverage import FireLogUnreadable, not_captured
from fno.budget.report import meter_lines, stop_rule_lines
from fno.budget.session_roster import SessionRoster
from fno.budget.stop_rule_tracker import review_date
from fno.budget.usage_export import ExportFileUsageReader
from fno.budget.usage_ledger import Attribution, UsageLedger, session_key
from fno.budget.wiring import build_month_meter
from fno.config import ROOT, load_app_config
from fno.research_data.calendar import CsvSessionCalendar
from tests.budget.exports import SESSION_ID, TWO_DAYS, export, result_event, write_export

COSTS = "month,item,category,amount_rs,source\n2026-10,Claude subscription,ai,1700,owner\n2026-10,Paid data,data,99,x\n"


TODAY = date(2026, 10, 16)


def config(**budget):
    """The app's settings with the decided plan cost and the data routines off, unless a test turns them on: each has
    its own tests below."""
    settings = load_app_config()
    settings["budget"] |= {"plan_cost": None, "data_routines": []} | budget
    return settings


DEV_IN_ROSTER = {"session_id": "session_01DEVabc", "created_at": "2026-10-14T09:00:00+05:30",
                 "updated_at": "2026-10-14T12:00:00+05:30", "captured_at": "2026-10-16T08:00:00+05:30"}  # fmt: skip
FIRED_LINK = f"https://claude.ai/code/cse_{SESSION_ID.split('_', 1)[1]}"  # the same session as the export


def repo(tmp_path, costs=COSTS, fired_session=FIRED_LINK):
    (tmp_path / "accounting").mkdir()
    (tmp_path / "accounting/operating_costs.csv").write_text(costs, encoding="utf-8")
    days = ExportFileUsageReader(write_export(tmp_path, export(TWO_DAYS))).days()  # 3 minutes over 14-15 Oct
    UsageLedger(tmp_path).record(days, Attribution("books_and_roles", "book2_hybrid"), date(2026, 10, 16))
    builder = export([result_event("2026-10-14T05:00:00Z", 180_000, "d1")])
    builder["session"]["ccr"]["id"] = "session_01DEVabc"
    days = ExportFileUsageReader(write_export(tmp_path, builder)).days()  # 3 minutes on 14 Oct
    UsageLedger(tmp_path).record(days, Attribution("development", "", "builder"), date(2026, 10, 16))
    SessionRoster(tmp_path).record([DEV_IN_ROSTER])
    log = tmp_path / "research/forecasts/ai_v1/2026/2026-10-14_fired.json"
    log.parent.mkdir(parents=True)
    entries = {"book2_hybrid": {"fired": True, "session": fired_session}, "book3_ai": {"fired": True, "session": ""}}
    log.write_text(json.dumps(entries), encoding="utf-8")
    return tmp_path


def test_the_meter_keeps_cash_spend_and_allocated_cost_apart(tmp_path):
    lines = meter_lines(build_month_meter("2026-10", TODAY, repo(tmp_path), config()))
    text = "\n".join(lines)
    assert "Claude subscription: cash spend Rs 1,700.00" in text
    assert "allocated, not a bill (minutes_share_v1)" in text and "books_and_roles book2_hybrid: Rs 850.00" in text
    assert "builder (development, not a book cost): Rs 850.00" in text
    assert "Azure Database for PostgreSQL: cash spend not recorded" in text
    assert "NEEDS OWNER: 2026-10 Paid data Rs 99.00" in text
    assert "3.00 of 3.00 minutes = 100.0%; level stop" in text and "plan's real capacity is not measurable" in text
    assert "development capture: complete" in text
    assert "WARNING: 1 fired AI book session(s) not captured: book shares understated" in text


def test_a_month_without_the_plan_cost_shows_unknown(tmp_path):
    text = "\n".join(meter_lines(build_month_meter("2026-10", TODAY, repo(tmp_path, COSTS.splitlines()[0] + "\n"),
                                                   config())))  # fmt: skip
    assert "no Claude plan cost recorded; allocation unknown" in text and "Rs 0.00" not in text


def test_fired_sessions_without_a_usage_row_are_counted_and_the_level_says_lower_bound(tmp_path):
    root = repo(tmp_path)
    meter = build_month_meter("2026-10", TODAY, root, config())
    assert [m[1] for m in meter.missing_captures] == ["book3_ai"]  # book2's session matched; book3 had no link
    assert "at least this level: 1 fired AI book session(s) not captured" in "\n".join(meter_lines(meter))
    assert len(not_captured(root, "2026-10", [], "2026-10-16")) == 2
    assert not_captured(root, "2026-11", [], "2026-11-30") == []
    assert not_captured(root, "2026-10", [], "2026-10-14") == []  # today's sessions cannot be captured yet


@pytest.mark.parametrize("text", ["[]", '{"book2_hybrid": "yes"}', ""])
def test_an_odd_fire_log_is_refused_naming_the_file(tmp_path, text):
    log = repo(tmp_path) / "research/forecasts/ai_v1/2026/2026-10-13_fired.json"
    log.write_text(text, encoding="utf-8")
    with pytest.raises(FireLogUnreadable, match="2026-10-13_fired.json"):
        not_captured(tmp_path, "2026-10", [], "2026-10-16")


def test_session_links_and_ids_match_on_the_part_after_the_prefix():
    assert session_key("https://claude.ai/code/cse_01AbC") == session_key("session_01AbC") == "01AbC"


def test_the_stop_rule_lines_say_projected_days_left_and_missing_inputs(tmp_path):
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)  # the root is a repository, as in production
    calendar = CsvSessionCalendar("date,kind,description,source_url\n2026-01-26,holiday,R,https://example.org/c\n")
    lines = stop_rule_lines(tmp_path, review_date(None, "2026-11", calendar), date(2026, 10, 15))
    text = "\n".join(lines)
    assert "review date: 31 May 2027 (projected" in text and "228 days from 2026-10-15" in text
    assert text.count("not computable yet") == 2 and "(story G6)" in text and "no_economic_test" in text


def test_a_purpose_without_rows_says_no_rows_not_zero(tmp_path):
    meter = build_month_meter("2026-11", TODAY, repo(tmp_path), config())
    assert "measured development: no rows recorded (unknown, not zero)" in "\n".join(meter_lines(meter))


def test_without_a_fresh_roster_the_level_is_unknown_and_book_shares_are_overstated(tmp_path):
    root = repo(tmp_path)
    (root / "accounting/ai_session_roster.csv").unlink()
    text = "\n".join(meter_lines(build_month_meter("2026-10", TODAY, root, config())))
    assert "level unknown" in text and "no session roster read since 2026-10-16T00:00:00+05:30" in text
    assert "development not checked: no session roster read since" in text and "book shares overstated" in text


def test_tokens_are_not_available_when_any_row_lacks_them(tmp_path):
    root = repo(tmp_path)
    text = "\n".join(meter_lines(build_month_meter("2026-10", TODAY, root, config())))
    assert "measured books_and_roles: 3.00 minutes, 1 session(s), output tokens 300" in text
    path = root / "accounting/ai_usage.csv"
    path.write_text(path.read_text(encoding="utf-8").replace(",100,", ",,", 1), encoding="utf-8")
    text = "\n".join(meter_lines(build_month_meter("2026-10", TODAY, root, config())))
    assert "measured books_and_roles: 3.00 minutes, 1 session(s), output tokens not available" in text


RECORDER = [{"name": "3 pm quote recorder", "schedule": "daily"}]


def test_missing_data_routine_runs_make_the_measured_level_unknown(tmp_path):
    """Judge 104 addendum 1: uncaptured data-routine minutes would raise the books' share, so the level is unknown
    until every expected run is recorded. Addendum 2: the 3 pm recorder is started every calendar day (CLAUDE.md), so
    1-15 Oct expects 15 runs, weekends and the 2 Oct holiday included."""
    root = repo(tmp_path)
    meter = build_month_meter("2026-10", TODAY, root, config(data_routines=RECORDER))
    text = "\n".join(meter_lines(meter))
    assert meter.cap.level == "unknown" and "0 of 15 expected run(s) recorded (3 pm quote recorder (daily))" in text
    owner = build_month_meter("2026-10", TODAY, root, config(data_routines=RECORDER, plan_minutes_per_month=600))
    # the owner's figure does not depend on the measured denominator: only the missed book session is named
    assert owner.cap.note.startswith("unknown: 1 fired AI book session(s)") and "data routines" not in owner.cap.note


def test_recorded_daily_runs_complete_the_coverage_and_only_the_routines_own_rows_count():
    from datetime import timedelta

    from fno.budget.routine_coverage import DataRoutine, routine_gap

    recorder = DataRoutine.from_config(RECORDER)
    days = [date(2026, 10, 1) + timedelta(days=n) for n in range(15)]
    rows = [{"purpose": "data_routines", "role_or_bundle": "3 pm quote recorder", "date": d.isoformat()} for d in days]
    assert routine_gap(recorder, rows, "2026-10", TODAY) == ""
    assert "14 of 15" in routine_gap(recorder, rows[1:], "2026-10", TODAY)  # 1 Oct, a session day, missing
    weekend = [row for row in rows if row["date"] != "2026-10-04"]  # a Sunday: the routine still runs
    assert "14 of 15" in routine_gap(recorder, weekend, "2026-10", TODAY)
    other = [row | {"purpose": "development"} for row in rows]
    assert "0 of 15" in routine_gap(recorder, other, "2026-10", TODAY)
    assert routine_gap([], [], "2026-10", TODAY) == ""


def test_a_month_outside_the_session_calendar_is_still_checked_and_fails_closed():
    """Addendum 2 SF2: no calendar lookup is left in this check (the schedule is daily), so a 2027 month cannot slip
    through as "complete"; with no runs recorded it reads as a gap."""
    from fno.budget.routine_coverage import DataRoutine, routine_gap

    gap = routine_gap(DataRoutine.from_config(RECORDER), [], "2027-01", date(2027, 2, 1))
    assert gap.startswith("data routines not fully captured: 0 of 31 expected run(s)")


@pytest.mark.parametrize("entry", ["3 pm quote recorder", {"name": "x", "schedule": "weekdays"}, {"schedule": "daily"}])
def test_a_routine_without_a_known_schedule_is_refused(entry):
    from fno.budget.routine_coverage import DataRoutine

    with pytest.raises(ValueError, match="needs a name and a schedule from"):
        DataRoutine.from_config([entry])


def test_the_decided_plan_cost_applies_to_every_month_from_october(tmp_path):
    """Judge 104 addendum 1 minor: the owner's INR 20,000 a month, from one config value citing its row."""
    root = repo(tmp_path, costs=COSTS.splitlines()[0] + "\n")
    (root / "docs").mkdir()
    (root / "docs/DESK_DECISIONS.md").write_text((ROOT / "docs/DESK_DECISIONS.md").read_text("utf-8"), "utf-8")
    decided = config(plan_cost=load_app_config()["budget"]["plan_cost"])
    november = "\n".join(meter_lines(build_month_meter("2026-11", TODAY, root, decided)))
    assert "cash spend Rs 20,000.00 (decided monthly fee (DESK_DECISIONS 15 Oct 2026: Claude plan cost" in november
    assert "not allocated yet (no measured usage this month): Rs 20,000.00" in november
    october = build_month_meter("2026-10", TODAY, root, decided)
    assert sum(october.allocation.allocated_rs.values()) == 20000.0
    september = "\n".join(meter_lines(build_month_meter("2026-09", TODAY, root, decided)))
    assert "cash spend not recorded" in september and "no Claude plan cost recorded" in september

"""Story BG1 criteria 1, 3 and 7 end to end: the meter built from a repository's files, with the allocation apart from
cash spend, the cap basis and its limits, and missing captures of fired AI book sessions."""

import json
from datetime import date

import pytest

from fno.budget.capture_coverage import FireLogUnreadable, not_captured
from fno.budget.report import meter_lines, stop_rule_lines
from fno.budget.stop_rule_tracker import review_date
from fno.budget.usage_export import ExportFileUsageReader
from fno.budget.usage_ledger import Attribution, UsageLedger, session_key
from fno.budget.wiring import build_month_meter
from fno.config import load_app_config
from fno.research_data.calendar import CsvSessionCalendar
from tests.budget.exports import SESSION_ID, TWO_DAYS, export, result_event, write_export

COSTS = "month,item,category,amount_rs,source\n2026-10,Claude subscription,ai,1700,owner\n2026-10,Paid data,data,99,x\n"


TODAY = date(2026, 10, 16)
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
    log = tmp_path / "research/forecasts/ai_v1/2026/2026-10-14_fired.json"
    log.parent.mkdir(parents=True)
    entries = {"book2_hybrid": {"fired": True, "session": fired_session}, "book3_ai": {"fired": True, "session": ""}}
    log.write_text(json.dumps(entries), encoding="utf-8")
    return tmp_path


def test_the_meter_keeps_cash_spend_and_allocated_cost_apart(tmp_path):
    lines = meter_lines(build_month_meter("2026-10", TODAY, repo(tmp_path), load_app_config()))
    text = "\n".join(lines)
    assert "Claude subscription: cash spend Rs 1,700.00" in text
    assert "allocated, not a bill (minutes_share_v1)" in text and "books_and_roles book2_hybrid: Rs 850.00" in text
    assert "development builder: Rs 850.00" in text
    assert "Azure Database for PostgreSQL: cash spend not recorded" in text
    assert "NEEDS OWNER: 2026-10 Paid data Rs 99.00" in text
    assert "3.00 of 3.00 minutes = 100.0%; level stop" in text and "plan's real capacity is not measurable" in text


def test_a_month_without_the_plan_cost_shows_unknown(tmp_path):
    text = "\n".join(meter_lines(build_month_meter("2026-10", TODAY, repo(tmp_path, COSTS.splitlines()[0] + "\n"),
                                                   load_app_config())))  # fmt: skip
    assert "no Claude plan cost recorded; allocation unknown" in text and "Rs 0.00" not in text


def test_fired_sessions_without_a_usage_row_are_counted_and_the_level_says_lower_bound(tmp_path):
    root = repo(tmp_path)
    meter = build_month_meter("2026-10", TODAY, root, load_app_config())
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
    calendar = CsvSessionCalendar("date,kind,description,source_url\n2026-01-26,holiday,R,https://example.org/c\n")
    lines = stop_rule_lines(tmp_path, review_date(None, "2026-11", calendar), date(2026, 10, 15))
    text = "\n".join(lines)
    assert "review date: 31 May 2027 (projected" in text and "228 days from 2026-10-15" in text
    assert text.count("not computable yet") == 2 and "(story G6)" in text and "no_economic_test" in text


def test_a_purpose_without_rows_says_no_rows_not_zero(tmp_path):
    meter = build_month_meter("2026-11", TODAY, repo(tmp_path), load_app_config())
    assert "measured development: no rows recorded (unknown, not zero)" in "\n".join(meter_lines(meter))

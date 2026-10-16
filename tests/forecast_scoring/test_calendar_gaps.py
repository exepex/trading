"""Response 241, option A (owner, 16 Oct 2026): live days whose risk-neutral baseline is empty only because the 45-day
calendar window crossed into an uncovered year are labelled "baseline missing: calendar", in G4's report and its weekly
summary. Built from the real 15 Oct 2026 live records, re-dated."""

import json
from datetime import date

from fno.config import ROOT
from fno.forecast.capture import LIVE_FOLDER
from fno.forecast_scoring.calendar_gaps import LABEL, calendar_limited_days
from fno.forecast_scoring.score_report import ReportContext, report_document, weekly_summary

REAL = (ROOT / LIVE_FOLDER / "2026" / "2026-10-15_forecasts.csv").read_text(encoding="utf-8")
COMPLETE_PACK = {"problems": [], "iv30": {"points": 14.2}}


def live_day(folder, day: date, pack: dict, rn_probability: str = "") -> None:
    """The real records re-dated to `day`; baseline A's Q1 and Q2 empty unless `rn_probability` is given."""
    lines = [line.replace("2026-10-15", day.isoformat()) for line in REAL.splitlines()]
    if rn_probability:
        lines = [line.replace(",,baseline_a_risk_neutral/v1", f",{rn_probability},baseline_a_risk_neutral/v1")
                 if line.startswith("baseline_a_risk_neutral") else line for line in lines]  # fmt: skip
    year = folder / f"{day:%Y}"
    year.mkdir(parents=True, exist_ok=True)
    (year / f"{day.isoformat()}_forecasts.csv").write_text("\n".join(lines) + "\n", encoding="utf-8")
    (year / f"{day.isoformat()}_pack.json").write_text(json.dumps(pack), encoding="utf-8")


def test_only_days_whose_sole_missing_input_is_the_calendar_target_are_labelled(tmp_path):
    live_day(tmp_path, date(2026, 11, 17), COMPLETE_PACK)  # 17 Nov + 45 days is in 2027: labelled
    live_day(tmp_path, date(2026, 11, 16), COMPLETE_PACK)  # 16 Nov + 45 days is 31 Dec: the calendar covered it
    live_day(
        tmp_path, date(2026, 11, 18), {"problems": ["no NIFTY futures observed by 15:00"], "iv30": {"points": 14.2}}
    )
    live_day(tmp_path, date(2026, 11, 19), COMPLETE_PACK, rn_probability="0.55")  # baseline A present
    assert calendar_limited_days(tmp_path) == [
        {"day": "2026-11-17", "questions": ["q1_nifty_up_20d", "q2_nifty_move_3pct_20d"], "label": LABEL}]  # fmt: skip


def test_a_day_that_does_not_match_its_receipt_is_left_out(tmp_path):
    live_day(tmp_path, date(2026, 11, 17), COMPLETE_PACK)
    assert calendar_limited_days(tmp_path, unverified=["2026-11-17"]) == []


def test_the_weekly_summary_names_the_days_and_an_older_report_without_the_field_still_reads():
    document = report_document(ReportContext(date(2026, 12, 4), {}, False, 0, ()), [])
    assert not any(LABEL in line for line in weekly_summary(document))  # a report written before the field existed
    document["calendar_limited_days"] = [{"day": "2026-11-17", "questions": ["q1_nifty_up_20d"], "label": LABEL}]
    line = next(line for line in weekly_summary(document) if LABEL in line)
    assert line == "Book 1's Q1 and Q2 averaged two baselines on 1 live days (baseline missing: calendar): 2026-11-17"

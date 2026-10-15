"""R2 end to end on synthetic NSE files: events to the answer, the report, and the legacy lot derivation."""

from datetime import date, datetime, timedelta

import pytest
from r2_synthetic import (
    CHARGES,
    chain_rows,
    future_row,
    legacy_name,
    legacy_row,
    quoted,
    udiff_name,
    weekdays,
    zipped,
)
from r2study.analysis import Inputs, MissingFile, run
from r2study.bhav import summarise
from r2study.events import Meeting
from r2study.lots import LegacyLots, agreed_lot, validate_derivation
from r2study.report import results_json, results_markdown
from r2study.sessions import Sessions
from r2study.sources import CorporateActions, SymbolNames

from fno.fo_bhavcopy import COLUMNS

DAYS = weekdays(date(2024, 10, 1), date(2025, 1, 10))
EXPIRIES = [date(2024, 10, 31), date(2024, 11, 28), date(2024, 12, 26), date(2025, 1, 30), date(2025, 2, 27)]


def day_rows(day: date, lot_of) -> list[dict]:
    rows = []
    for expiry in [e for e in EXPIRIES if e >= day][:3]:
        lot = lot_of(day, expiry)
        rows.append(future_row(day, "ABC", expiry, 1000.0, lot))
        rows.append(future_row(day, "NOOPT", expiry, 500.0, 50))  # futures only: not an F&O stock here
        rows.extend(chain_rows(day, "ABC", expiry, 1000.0, 20.0, lot))
    return rows


def inputs(lot=100, snapshot=True, meetings=None, lot_of=None, filed=None, missing=()) -> Inputs:
    lot_of = lot_of or (lambda day, expiry: lot)
    files = {day: (udiff_name(day), zipped(udiff_name(day), day_rows(day, lot_of), COLUMNS)) for day in DAYS}
    for day in missing:
        del files[day]
    names = SymbolNames([])
    return Inputs(
        sessions=Sessions(DAYS),
        current=files.get,
        legacy=lambda day: None,
        nifty=lambda day: 24000.0,
        meetings=meetings
        or [
            Meeting("ABC", date(2024, 10, 22), "Financial Results"),
            Meeting("NOOPT", date(2024, 10, 22), "Financial Results"),
            Meeting("ABC", date(2025, 1, 7), "Financial Results"),
        ],
        filing_times={"ABC": [(filed or datetime(2024, 10, 22, 17, 0), date(2024, 9, 30))]},
        sectors={"ABC": "Information Technology"},
        names=names,
        actions=CorporateActions([], names),
        charges=CHARGES,
        snapshot=[quoted(s, c, spread=0.001) for s in (0, 1, 2) for c in range(40)] if snapshot else None,
    )


def by_name(out: dict) -> dict:
    return {s.name[:2]: s for s in out["structures"]}


def test_a_fitting_liquid_cheap_event_still_fails_on_clusters_a_year():
    out = run(inputs())
    assert out["answer"]["answer"] == "NO" and out["answer"]["stage"] == "stopped at stage 4 (clusters)"
    s1 = by_name(out)["S1"]
    assert (s1.events, s1.stage1_share, s1.stage2_share, s1.stage3_share) == (1, 1.0, 1.0, 1.0)
    assert s1.median_net > 0 and s1.clusters == 1
    assert s1.clusters_a_year == 1 / ((DAYS[-1] - date(2024, 10, 1)).days + 1) * 365.25
    assert out["events"]["left_out_before_events"]["not F&O on the entry session"] == 1
    assert out["events"]["decision_window_with_filed_at"] == 0.5  # the January meeting has no filing
    assert out["stage0"]["coverage"]["share"] == 1.0 and out["stage0"]["passes"]


def test_without_the_snapshot_the_answer_waits_for_spread_evidence():
    out = run(inputs(snapshot=False))
    assert out["answer"] == {"answer": "CANNOT ANSWER", "stage": "stopped before stage 3",
                             "reason": "cannot answer yet: no spread evidence"}  # fmt: skip
    assert by_name(out)["S1"].stage3_share is None


def test_a_large_lot_stops_every_structure_at_the_cap():
    out = run(inputs(lot=3000))
    assert out["answer"]["stage"] == "stopped at stage 1 (cap)"
    assert all(s.stage1_share == 0.0 for s in out["structures"])


def test_too_few_results_dates_cannot_answer_at_stage_0():
    out = run(inputs(meetings=[Meeting("ABC", date(2025, 1, 7), "Financial Results")]))
    assert out["answer"]["answer"] == "CANNOT ANSWER" and out["answer"]["stage"] == "stage 0"
    assert "results dates" in out["answer"]["reason"]
    assert out["stage0"]["coverage"]["share"] == 0.0


def test_report_names_the_answer_the_trial_and_the_assumed_hurdle():
    out = results_json(run(inputs()), 53, "abc123")
    text = results_markdown(out)
    assert out["trial"] == "trial 53 of 53" and out["clusters_a_year_rule"] == {"registered": 130, "power_80": 297}
    assert "**Answer: NO**" in text and "assumed hurdle" in text and "S7 short iron condor" in text


def legacy_pair(day: date, lot: int, turnover_scale: float = 1.0):
    rows = [future_row(day, "ABC", date(2024, 1, 25), 1000.0, lot)] + chain_rows(
        day, "ABC", date(2024, 1, 25), 1000, 20, lot
    )
    old = [legacy_row(day, r) for r in rows]
    old[0]["VAL_INLAKH"] *= turnover_scale
    legacy_columns = list(old[0])
    current = summarise(day, udiff_name(day), zipped(udiff_name(day), rows, COLUMNS))
    legacy = summarise(day, legacy_name(day), zipped(legacy_name(day), old, legacy_columns))
    return current, legacy


def test_legacy_lot_derivation_validates_only_on_exact_matches():
    days = weekdays(date(2024, 1, 1), date(2024, 1, 12))
    sessions = Sessions(days)
    exact = {d: legacy_pair(d, 250) for d in days}
    check = validate_derivation(sessions, days[2:], lambda d: exact[d][0], lambda d: exact[d][1])
    assert check["share"] == 1.0 and check["valid"]
    # the first two sessions have fewer than 3 derived values behind them: no agreed lot, counted as misses
    assert validate_derivation(sessions, days, lambda d: exact[d][0], lambda d: exact[d][1])["share"] == 0.8
    off = {d: legacy_pair(d, 250, 1.01) for d in days}  # turnover 1% off: derived lot 252, never 250
    check = validate_derivation(sessions, days, lambda d: off[d][0], lambda d: off[d][1])
    assert check["share"] == 0.0 and not check["valid"]
    assert LegacyLots(sessions, lambda d: exact[d][1]).derived("ABC", days[-1], date(2024, 1, 25)) == 250
    assert LegacyLots(sessions, lambda d: exact[d][1]).derived("ABC", days[-1], date(2024, 2, 29)) is None
    assert validate_derivation(sessions, [], lambda d: None, lambda d: None)["valid"] is False


def test_agreed_lot_needs_the_same_value_on_three_of_five_sessions():
    assert agreed_lot([250, 250, 250, None, 300]) == 250
    assert agreed_lot([250, 250, None, 300, 300]) is None
    assert agreed_lot([]) is None and agreed_lot([None] * 5) is None


def big_next_month(day, expiry):
    return 3000 if expiry >= date(2024, 11, 28) else 100  # a lot revision that applies to the next months only


def test_the_lot_is_the_chosen_expirys_own_not_the_near_months():
    near = run(inputs(lot_of=big_next_month))  # R 23 Oct: the October expiry, lot 100
    assert by_name(near)["S1"].stage1_share == 1.0
    pushed = run(inputs(lot_of=big_next_month, filed=datetime(2024, 10, 25, 17, 0),
                        meetings=[Meeting("ABC", date(2024, 10, 25), "Financial Results")]))  # fmt: skip
    assert by_name(pushed)["S1"].events == 1 and by_name(pushed)["S1"].stage1_share == 0.0  # November, lot 3000


def test_a_lot_change_of_the_traded_contract_on_r_is_a_corporate_action():
    def changed(day, expiry):
        return 200 if day >= date(2024, 10, 23) else 100

    out = run(inputs(lot_of=changed))
    assert out["events"]["left_out_all_years"] == {"corporate action": 1, "no expiry at least 5 sessions after R": 1}
    assert out["events"]["decision_window_analysed"] == 0


def test_a_session_without_its_file_stops_the_run():
    with pytest.raises(MissingFile):
        run(inputs(missing=[date(2024, 10, 22)]))


def test_events_before_the_period_are_counted_not_analysed(monkeypatch):
    import r2study.analysis as analysis

    monkeypatch.setattr(analysis, "PERIOD_START", date(2024, 10, 24))  # the October event's R (23 Oct) is now before
    out = run(inputs())
    assert out["events"]["left_out_before_events"]["reaction session before 1 Jan 2019"] == 1
    assert by_name(out)["S1"].events == 0


def test_the_studys_sessions_count_calendar_sessions_after_the_last_file():
    from r2study.wiring import sessions_from_manifests

    sessions = sessions_from_manifests(log=lambda line: None)  # manifests and the calendar only: no study data
    assert sessions.between(sessions.last, sessions.last + timedelta(days=30)) >= 15

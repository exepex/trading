"""R2 end to end on synthetic NSE files: events to the answer, the report, and the legacy lot derivation."""

from datetime import date, datetime

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
from r2study.analysis import Inputs, run
from r2study.bhav import summarise
from r2study.events import Meeting
from r2study.lots import LotSizes, agreed_lot, validate_derivation
from r2study.report import results_json, results_markdown
from r2study.sessions import Sessions
from r2study.sources import CorporateActions, SymbolNames

from fno.fo_bhavcopy import COLUMNS

DAYS = weekdays(date(2024, 10, 1), date(2025, 1, 10))
EXPIRIES = [date(2024, 10, 31), date(2024, 11, 28), date(2024, 12, 26), date(2025, 1, 30), date(2025, 2, 27)]


def day_rows(day: date, lot: int) -> list[dict]:
    rows = []
    for expiry in [e for e in EXPIRIES if e >= day][:3]:
        rows.append(future_row(day, "ABC", expiry, 1000.0, lot))
        rows.append(future_row(day, "NOOPT", expiry, 500.0, 50))  # futures only: not an F&O stock here
        rows.extend(chain_rows(day, "ABC", expiry, 1000.0, 20.0, lot))
    return rows


def inputs(lot=100, snapshot=True, meetings=None) -> Inputs:
    files = {day: (udiff_name(day), zipped(udiff_name(day), day_rows(day, lot), COLUMNS)) for day in DAYS}
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
        filing_times={"ABC": [datetime(2024, 10, 22, 17, 0)]},
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
    assert out["events"]["left_out_by_reason"]["not F&O on the entry session"] == 1
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
    assert out["answer"] == {"answer": "CANNOT ANSWER", "stage": "stage 0"}
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
    lots = LotSizes(sessions, lambda d: None, lambda d: exact[d][1], legacy_valid=False)
    assert lots.lot("ABC", days[-1]) is None  # the derivation did not validate: lot unknown
    assert validate_derivation(sessions, [], lambda d: None, lambda d: None)["valid"] is False


def test_agreed_lot_needs_the_same_value_on_three_of_five_sessions():
    assert agreed_lot([250, 250, 250, None, 300]) == 250
    assert agreed_lot([250, 250, None, 300, 300]) is None
    assert agreed_lot([]) is None and agreed_lot([None] * 5) is None

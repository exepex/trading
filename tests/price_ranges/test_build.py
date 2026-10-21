"""G13b criteria 1-2 and 4: a 15:45 record point in time (only the day's chain and closes before the day; a planted
close of the day or later changes nothing), stale closes, N1 and N3 on the calendar with τ = k + 0.049, no N0, the
calendar's end, the end-of-day basis, and the record check."""

from datetime import date, timedelta

import pytest

from fno.forecast_v4_rules.series import DayValue
from fno.price_ranges.build import CAPTURE, CLOSE
from fno.price_ranges.constants import MISSING, NOT_ELIGIBLE, OK, REST_OF_DAY, RULE_FORECASTERS
from fno.price_ranges.records import RecordRefused, check_row, encode
from tests.price_distribution.builders import DAY, chain_day
from tests.price_ranges.builders import builder, closes

HISTORY = closes()


def build(history=HISTORY, chain=None, basis=CAPTURE, day=DAY):
    return builder().build("NIFTY", day, "1545", chain if chain is not None else chain_day(day=day), history, basis,
                           "live", "2026-10-16T15:45:00+05:30")  # fmt: skip


def test_a_good_day_has_every_rule_forecaster_at_n1_and_n3_and_no_n0():
    record = build()
    assert {(r["forecaster"], r["horizon"]) for r in record["rows"]} == {(f, h) for f in RULE_FORECASTERS
                                                                           for h in ("N1", "N3")}  # fmt: skip
    assert record["status"] == OK and record["s_ref"] == 22_990.0 and record["s_ref_at"].startswith("2026-10-16T14:55")


def test_targets_skip_the_holiday_and_tau_adds_the_rest_of_the_day():
    rows = {r["horizon"]: r for r in build()["rows"] if r["forecaster"] == "rv20"}
    assert rows["N1"]["target_day"] == "2026-10-19" and rows["N3"]["target_day"] == "2026-10-22"  # 20th a holiday
    assert rows["N1"]["tau"] == pytest.approx(1 + REST_OF_DAY) and rows["N3"]["tau"] == pytest.approx(3.0486, abs=1e-4)


def test_no_close_of_the_day_or_later_is_read_at_15_45():
    planted = [*HISTORY, DayValue(DAY, 99_999.0), DayValue(DAY + timedelta(days=3), 1.0)]
    assert encode(build()) == encode(build(planted))


def test_stale_closes_make_the_close_based_forecasters_missing():
    record = build([c for c in HISTORY if c.day < DAY - timedelta(days=3)])
    by = {(r["forecaster"], r["horizon"]): r for r in record["rows"]}
    assert {by[(f, "N1")]["status"] for f in ("rv20", "hist750", "ewma_t4")} == {MISSING}
    assert by[("rv20", "N1")]["reason"].startswith("closes stale")
    assert by[("implied", "N1")]["status"] == OK and record["status"] == "problems"


def test_no_chain_or_no_spot_is_a_missing_issue():
    no_spot = build(chain=chain_day(spot=None))
    assert no_spot["status"] == MISSING and no_spot["problems"] == ["no reference price: no 3 pm chain with a spot"]


def test_past_the_calendar_s_end_is_not_eligible():
    day = date(2026, 12, 31)
    record = build(closes(last=day - timedelta(days=1)), chain_day(day=day), day=day)
    assert {r["status"] for r in record["rows"]} == {NOT_ELIGIBLE}
    assert all("calendar ends" in r["reason"] for r in record["rows"])


def test_the_end_of_day_basis_uses_the_day_s_close_and_tau_k():
    history = closes(last=DAY)
    record = build(history, basis=CLOSE)
    assert record["s_ref"] == history[-1].value and record["closes_through"] == DAY.isoformat()
    assert {r["tau"] for r in record["rows"]} == {1.0, 3.0}
    assert build(HISTORY, basis=CLOSE)["status"] == MISSING  # no close of the day: no reference


def row(**changes):
    base = {"forecaster": "implied", "horizon": "N1", "status": OK, "reason": None, "p_up": 0.5}
    return base | {f"lq{n:02d}": v for n, v in zip((5, 25, 50, 75, 95), range(5), strict=True)} | changes


@pytest.mark.parametrize(
    ("changes", "message"),
    [
        ({"lq50": 1}, "strictly increasing"),
        ({"forecaster": "no_change"}, "point mass"),
        ({"p_up": 1.2}, "P\\(up\\)"),
        ({"horizon": "N2"}, "unknown forecaster or horizon"),
        ({"status": MISSING}, "needs its reason"),
    ],
)
def test_the_record_check_refuses_bad_rows(changes, message):
    with pytest.raises(RecordRefused, match=message):
        check_row(row(**changes))


def test_the_record_check_accepts_a_point_mass_for_no_change_only():
    check_row(
        row(forecaster="no_change", **{f"lq{n:02d}": 0.0 for n in (5, 25, 50, 75, 95)})
    )  # issues: judge 416 tests

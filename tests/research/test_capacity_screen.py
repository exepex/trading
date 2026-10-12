"""Rules of the NIFTY capacity screen (ChatGPT review 4, sections 4-6)."""

import importlib.util
import sys
from datetime import date
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[2] / "research" / "2026-10-12-capacity-screen" / "screen.py"
spec = importlib.util.spec_from_file_location("capacity_screen", SCRIPT)
screen = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = screen
spec.loader.exec_module(screen)

NO_CHARGES = {
    "brokerage_per_order": 0,
    "stt_sell_pct": 0,
    "exchange_txn_pct": 0,
    "sebi_per_crore": 0,
    "ipft_per_crore": 0,
    "stamp_duty_buy_pct": 0,
    "gst_pct": 0,
}
DAY = date(2026, 10, 9)
MONTHLY = {date(2026, 11, 24)}  # the monthly expiry listed on 12 Oct 2026 in these fixtures (43 days away)


def test_price_padding_is_counted_once_four_orders_times_pad_times_lot():
    raw = screen.admission(400.0, 372.0, 0.0, 65, NO_CHARGES)
    assert raw == 28.0 * 65
    assert screen.admission(400.0, 372.0, 1.0, 65, NO_CHARGES) - raw == 4 * 1.0 * 65  # Rs 260, not 520


def test_nearest_strike_ties_go_to_the_lower_strike():
    assert screen.nearest_strike(22375.0, [22350.0, 22400.0]) == 22350.0
    assert screen.nearest_strike(22380.0, [22350.0, 22400.0]) == 22400.0


def row(strike, kind, close, volume=10, expiry="2026-11-24"):
    return {
        "TradDt": "2026-10-12",
        "XpryDt": expiry,
        "StrkPric": str(strike),
        "OptnTp": kind,
        "ClsPric": str(close),
        "TtlTradgVol": str(volume),
        "UndrlygPric": "22370",
        "NewBrdLotQty": "65",
    }


def statuses(rows):
    out = screen.screen_day(date(2026, 10, 12), rows, MONTHLY, NO_CHARGES)
    return {(r["direction"], r["width"]): r["status"] for r in out if r["pad"] == 0.0}


def test_each_failure_has_its_own_reason_and_a_missing_price_is_not_a_cap_failure():
    rows = [row(22350, "CE", 400), row(22400, "CE", 372), row(22450, "CE", 0.0), row(22550, "CE", 300, volume=0)]
    rows += [row(22350, "PE", 300), row(22300, "PE", 310)]  # put debit below zero: prices not synchronous
    got = statuses(rows)
    assert got[("bull_call", 50)] == "priced"
    assert got[("bull_call", 100)] == "invalid_price"
    assert got[("bull_call", 200)] == "zero_volume_price_unusable"
    assert got[("bear_put", 50)] == "nonsynchronous_price_anomaly"
    assert got[("bear_put", 100)] == "missing_required_leg"


def test_priced_rows_record_admission_against_every_profile():
    out = screen.screen_day(date(2026, 10, 12), [row(22350, "CE", 400), row(22400, "CE", 372)], MONTHLY, NO_CHARGES)
    priced = next(r for r in out if r["direction"] == "bull_call" and r["width"] == 50 and r["pad"] == 2.0)
    assert priced["admission"] == 28 * 65 + 4 * 2 * 65
    assert priced["fits_2L_1pct"] == 0 and priced["fits_2L_2pct"] == 1
    bear = next(r for r in out if r["direction"] == "bear_put" and r["pad"] == 0.0)
    assert bear["status"] == "contract_unavailable"  # no puts listed for that expiry


def test_no_monthly_in_the_window_means_no_trade_even_if_a_weekly_is_priced():
    weekly_rows = [row(22350, "CE", 400, expiry="2026-11-17"), row(22400, "CE", 372, expiry="2026-11-17")]
    out = screen.screen_day(date(2026, 10, 12), weekly_rows, {date(2026, 12, 29)}, NO_CHARGES)
    assert {r["status"] for r in out} == {"no_eligible_expiry"}

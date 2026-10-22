"""Both runs on a synthetic market: run 1 never sees a price after its seal; run 2 tests only run 1's G1 passers (the
naked measurements are reported, never tested); Holm and the nomination see only tested variants."""

from datetime import date, timedelta

import edge1study.runs as runs
from edge1study.runner import RUN1_SEAL, Market
from edge1study.runs import run1, run2

from fno.research_data.panel_reader import FutureQuote, NiftyPanel, OptionQuote, SessionClose

CHARGES = {"brokerage_per_order": 20.0, "stt_sell_pct": 0.15, "stt_exercise_pct": 0.15, "exchange_txn_pct": 0.03503,
           "sebi_per_crore": 10, "ipft_per_crore": 50, "stamp_duty_buy_pct": 0.003, "gst_pct": 18}  # fmt: skip


class Calendar:
    def session_kind(self, day):
        return "regular" if day.weekday() < 5 else None

    def sessions(self, first, last):
        return [first + timedelta(days=i) for i in range((last - first).days + 1)
                if (first + timedelta(days=i)).weekday() < 5]  # fmt: skip


def last_thursday(year: int, month: int) -> date:
    day = date(year + month // 12, month % 12 + 1, 1) - timedelta(days=1)
    return day - timedelta(days=(day.weekday() - 3) % 7)


def market(first=date(2022, 9, 1), last=date(2023, 8, 31), crazy_after=None) -> Market:
    days = Calendar().sessions(first, last)
    expiries = sorted({last_thursday(y, m) for y in (2022, 2023, 2024) for m in range(1, 13)})
    sessions, options, futures, lots = [], {}, {}, {}
    for day in days:
        spot = 23000.0 * (5.0 if crazy_after and day > crazy_after else 1.0)
        live = [e for e in expiries if day <= e <= day + timedelta(days=95)]
        sessions.append(SessionClose(day, "regular", spot, None))
        options[day] = tuple(OptionQuote(e, float(k), kind, max(5.0, 150.0 - abs(k - spot) * 0.1) +
                                         max(0.0, (spot - k) if kind == "CE" else (k - spot)), 1.0, 10, 100)
                             for e in live for k in range(21000, 25100, 100) for kind in ("CE", "PE"))  # fmt: skip
        futures[day] = tuple(FutureQuote(e, spot, spot, 10, 100) for e in live)
        lots[day] = dict.fromkeys(live, 25)
    return Market("NIFTY", NiftyPanel(tuple(sessions), options, futures), lots, lambda expiry: 23000.0)


def no_margin(index, trades):
    return None


def test_run1_never_sees_a_price_after_its_seal():
    normal = run1({"NIFTY": market()}, Calendar(), CHARGES, no_margin, {"NIFTY": 8})
    crazy = run1({"NIFTY": market(crazy_after=RUN1_SEAL)}, Calendar(), CHARGES, no_margin, {"NIFTY": 8})
    assert normal == crazy and normal["NIFTY SC2 T21"]["pad1"]["cycles"] > 0
    assert normal["NIFTY SC2 T21"]["g1"]["passed"] is False  # far fewer than 20 run-1 trades
    assert "g1" not in normal["NIFTY NS T21"] and normal["NIFTY NS T21"]["tradeable"] is False


def test_run2_tests_only_g1_passers_and_holm_and_nomination_see_only_them(monkeypatch):
    selection = run1({"NIFTY": market()}, Calendar(), CHARGES, no_margin, {"NIFTY": 8})
    selection["NIFTY SC2 T21"]["g1"]["passed"] = True
    monkeypatch.setattr(runs, "one_sided_p", lambda nets, k: 0.001)
    found = run2({"NIFTY": market()}, Calendar(), CHARGES, no_margin, selection, {"NIFTY": date(2023, 8, 31)})
    assert found["tested"] == ["NIFTY SC2 T21"]
    assert set(found["variants"]) == {"NIFTY SC2 T21", "NIFTY NS T21", "NIFTY NT T21"}
    assert found["variants"]["NIFTY SC2 T21"]["holm"] is True and "holm" not in found["variants"]["NIFTY NS T21"]
    assert found["nominated"] in ([], ["NIFTY SC2 T21"])  # the nomination's own conditions decide the rest

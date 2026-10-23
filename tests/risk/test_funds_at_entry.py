"""Judge 77 addendum 3: C2 is never looser than Groww at entry. Groww's answer for NIFTY Nov 22700 short iron fly width
100, 1 lot of 65, on 14 Oct 2026 (read-only margin API, no order): SPAN 6,893.00 + exposure 58,819.02 + bought premium
47,450 + charges 150.62 = 113,312.64 free funds, with no credit for the sold premium (53,475.50) until settlement.

C2's netted margin room alone needed far less: it credits the entry's cash flow and nets the premium into SPAN, so it
would open a trade Groww refuses. The funds-at-entry check closes that: margin without the premium credit
(max(0, scan - NOV) + exposure, from the same NSE row: 822.25 + 6,071 = 6,893.25, Re 0.25 above Groww's rounded SPAN)
plus the bought premium and charges, against the free cash before entry. The mirror (a long iron fly, a debit) pays
the dearer legs and is not credited the cheaper ones."""

from datetime import date, timedelta

import pytest

from fno.risk.margin_age import DaysOld
from fno.risk.margins import MarginParts, MarginTable, MultiplierMargin
from fno.risk.rules import MarginRoom
from fno.risk.settings import StressedMarginSettings
from fno.storage.table_source import FileTable
from tests.stress_factor_files import factor_file

from .builders import DAY, START, book, market, open_trade, proposal, short_fly

EXPIRY = date(2026, 11, 23)
UNITS = 65
SOLD_PREMIUM, BOUGHT_PREMIUM, CHARGES = 53_475.50, 47_450.00, 150.62
GROWW_TOTAL = 6_893.00 + 58_819.02 + BOUGHT_PREMIUM + CHARGES
SF = MarginParts(822.25, -6_071.0, 58_819.02, "SF width 100")  # exposure on the 15:32 file's index, Groww's base
BF = MarginParts(831.35, 6_071.0, 58_819.02, "BF width 100")
MIDS = {(22700.0, "CE"): SOLD_PREMIUM / UNITS / 2, (22700.0, "PE"): SOLD_PREMIUM / UNITS / 2,
        (22800.0, "CE"): BOUGHT_PREMIUM / UNITS / 2, (22600.0, "PE"): BOUGHT_PREMIUM / UNITS / 2}  # fmt: skip
HEADER = "structure,width,scan_per_lot_rs,nov_per_lot_rs,exposure_per_lot_rs,source,as_of\n"


class GrowwCosts:
    """The entry as Groww priced it: the premium each side and its charges."""

    def __init__(self, paid: float, received: float):
        self.paid, self.received = paid, received

    def entry_cash_flow(self, prop, the_market):
        return self.received - self.paid - CHARGES

    def entry_funds(self, prop, the_market):
        return self.paid + CHARGES


def room(tmp_path, costs) -> MarginRoom:
    rows = [f"{p.what.split()[0]},100,{p.scan},{p.nov},{p.exposure},NSE SPAN i1,{DAY}\n" for p in (SF, BF)]
    (tmp_path / "margins.csv").write_text(HEADER + "".join(rows))
    settings = StressedMarginSettings("multiplier", factor_file(1.0, DAY - timedelta(days=1)), 30, None)
    return MarginRoom(
        MultiplierMargin(MarginTable(FileTable(tmp_path / "margins.csv"), DaysOld(7), 65), settings), costs
    )


def check(tmp_path, cash, debit=False):
    spec = short_fly(22700, 100)
    spec = [(k, kind, -side) for k, kind, side in spec] if debit else spec
    costs = GrowwCosts(SOLD_PREMIUM, BOUGHT_PREMIUM) if debit else GrowwCosts(BOUGHT_PREMIUM, SOLD_PREMIUM)
    new = proposal("new", "BF" if debit else "SF", 100, spec, EXPIRY)
    return room(tmp_path, costs).check(new, book([], cash=cash, marked=cash), market(22622.70, MIDS, EXPIRY, day=DAY))


def test_the_groww_basket_needs_its_full_funds_at_entry(tmp_path):
    needed = round(SF.at_entry(1.0) + BOUGHT_PREMIUM + CHARGES, 2)  # to the paisa, as cash is held
    assert needed == pytest.approx(6_893.25 + 58_819.02 + 47_600.62)
    assert needed - GROWW_TOTAL == pytest.approx(0.25)  # never looser: Groww rounds SPAN to the rupee
    allowed = check(tmp_path, needed)
    assert allowed.ok and allowed.numbers["needed_at_entry_rs"] == pytest.approx(needed)
    assert allowed.numbers["funds_at_entry_rs"] == pytest.approx(BOUGHT_PREMIUM + CHARGES)
    assert not check(tmp_path, needed - 0.01).ok


def test_a_rupee_below_groww_s_total_is_refused_though_the_netted_room_alone_passed_it(tmp_path):
    refused = check(tmp_path, GROWW_TOTAL - 1.0)
    netted_room = refused.numbers["available_after_entry_rs"] - refused.numbers["needed_rs"]
    assert not refused.ok and "above free cash" in refused.reason
    assert netted_room > 50_000  # the old check alone: about the sold premium looser than the broker


def test_the_mirror_debit_pays_the_dear_legs_and_is_not_credited_the_cheap_ones(tmp_path):
    needed = round(BF.at_entry(1.0) + SOLD_PREMIUM + CHARGES, 2)  # max(0, 831.35 - 6,071) = 0: exposure + legs bought
    assert needed == pytest.approx(58_819.02 + 53_475.50 + 150.62)
    assert check(tmp_path, needed, debit=True).ok
    refused = check(tmp_path, needed - 0.01, debit=True)
    assert not refused.ok and refused.numbers["available_after_entry_rs"] - refused.numbers["needed_rs"] > 40_000


def test_the_free_cash_before_entry_holds_back_pending_premium_and_each_losing_trade(tmp_path):
    """Two open flies far out of the money: a credit marked Rs 9,000 worse than zero and a debit worth Rs 9,000, so
    marked equity equals cash. A broker does not net one trade's value against the other's loss, and the premium
    reserved for pending orders is not free either."""
    out = {(23500.0, "CE"): 0.0, (23500.0, "PE"): 0.0, (23600.0, "CE"): 0.0, (23400.0, "PE"): 0.0}
    losing = {(21500.0, "CE"): 9_000.0 / UNITS, (21500.0, "PE"): 0.0, (21600.0, "CE"): 0.0, (21400.0, "PE"): 0.0}
    credit = open_trade("credit", "SF", 100, short_fly(21500, 100), EXPIRY, 0.0)
    debit = open_trade("debit", "BF", 100, [(k, kind, -s) for k, kind, s in short_fly(23500, 100)], EXPIRY, 0.0)
    marks = MIDS | out | losing | {(23500.0, "CE"): 9_000.0 / UNITS}
    held = book([credit, debit], cash=START, marked=START, premium_reserved=1_000.0)
    new = proposal("new", "SF", 100, short_fly(22700, 100), EXPIRY)
    verdict = room(tmp_path, GrowwCosts(BOUGHT_PREMIUM, SOLD_PREMIUM)).check(
        new, held, market(22622.70, marks, EXPIRY, day=DAY)
    )
    assert verdict.numbers["free_before_entry_rs"] == pytest.approx(START - 9_000.0 - 1_000.0)

"""Judge 75 (story A14): C2 counts max(0, scan - NOV) + min(0, NOV) + exposure, stresses the scan and the exposure,
never the premium (story C2c), refuses a margin not above 0, and with an open losing trade never leaves more free than
a broker that nets the premium."""

from datetime import date, timedelta

import pytest

from fno.research_engine.structures import BOUGHT, SOLD
from fno.risk.inputs import RiskInputError
from fno.risk.margin_age import DaysOld
from fno.risk.margins import MarginParts, MarginTable, MultiplierMargin
from fno.risk.rules import MarginRoom
from fno.risk.settings import StressedMarginSettings
from fno.storage.table_source import FileTable
from tests.stress_factor_files import factor_file

from .builders import DAY, START, book, market, open_trade, proposal, short_fly

EXPIRY = date(2026, 11, 23)
HEADER = "structure,width,scan_per_lot_rs,nov_per_lot_rs,exposure_per_lot_rs,source,as_of\n"
# The real 14 Oct 2026 parts (nsccl.20261014.i1, response 77): SF and BF width 100, per lot
SF_100 = MarginParts(822.25, -6071.0, 59077.07, "SF width 100")
BF_100 = MarginParts(831.35, 6071.0, 59077.07, "BF width 100")
# Mids giving those values: per unit -(50 + 50) + 3.3 + 3.3 = -93.4, x 65 = -6,071
MIDS = {(22700.0, "CE"): 50.0, (22700.0, "PE"): 50.0, (22800.0, "CE"): 3.3, (22600.0, "PE"): 3.3}


def test_a_credit_structure_counts_its_scan_risk_and_a_debit_its_netted_span():
    assert SF_100.initial() == pytest.approx(822.25 + 59077.07)  # (A): the premium is already out of free cash
    assert BF_100.initial() == pytest.approx(59077.07)  # (B): max(0, 831.35 - 6,071) = 0


def test_the_stress_factor_grows_the_scan_and_the_exposure_never_the_premium():
    assert SF_100.stressed(1.45) == pytest.approx(1.45 * (822.25 + 59077.07))  # 86,854.01 (was 60,269.33)
    assert BF_100.stressed(1.45) == pytest.approx(1.45 * 59077.07)  # 1.45 x 831.35 is still below the 6,071 paid
    big_debit = MarginParts(10_000.0, 6_000.0, 0.0, "BF")
    assert big_debit.stressed(1.5) == pytest.approx(15_000.0 - 6_000.0)  # k x (scan - NOV) would be 6,000: too loose


@pytest.mark.parametrize(
    "parts, reason",
    [((0.0, 500.0, 0.0), "must be above 0"), ((-1.0, 0.0, 100.0), "cannot be negative"),
     ((100.0, 0.0, -1.0), "cannot be negative")],
)  # fmt: skip
def test_a_margin_not_above_0_or_a_negative_part_is_refused_by_name(parts, reason):
    with pytest.raises(RiskInputError, match=reason):
        MarginParts(*parts, "BF width 100").initial()


def _room(tmp_path) -> MarginRoom:
    rows = [f"{p.what.split()[0]},100,{p.scan},{p.nov},{p.exposure},NSE SPAN test,{DAY}\n" for p in (SF_100, BF_100)]
    (tmp_path / "margins.csv").write_text(HEADER + "".join(rows))
    settings = StressedMarginSettings("multiplier", factor_file(1.0, DAY - timedelta(days=1)), 30, None)
    return MarginRoom(
        MultiplierMargin(MarginTable(FileTable(tmp_path / "margins.csv"), DaysOld(7), 65), settings), CostsAtMid()
    )


class CostsAtMid:
    """Entry at mid with no charges: the cash flow is minus the position's value; the funds are the bought legs."""

    def entry_cash_flow(self, prop, the_market):
        return -sum(units * the_market.quote(c).mid for c, units in prop.signed_units().items())

    def entry_funds(self, prop, the_market):
        return sum(units * the_market.quote(c).mid for c, units in prop.signed_units().items() if units > 0)


def _broker_margin(parts: MarginParts, nov_now: float) -> float:
    return max(0.0, parts.scan - nov_now) + parts.exposure  # a broker netting the premium, at the current value


def _held(side: int, loss: float):
    """A fly at 22,300 opened for Rs 6,071 (a short fly received it, a long fly paid it), now marked `loss` worse: the
    trade, its entry cash flow, its value now and the parts C2 reads for it."""
    value = -(6071.0 + loss) if side == SOLD else 6071.0 - loss
    spec = short_fly(22300, 100) if side == SOLD else [(k, kind, -s) for k, kind, s in short_fly(22300, 100)]
    marks = {(22300.0, "CE"): abs(value) / 65, (22300.0, "PE"): 0.0, (22400.0, "CE"): 0.0, (22200.0, "PE"): 0.0}
    parts = SF_100 if side == SOLD else BF_100
    trade = open_trade("open", parts.what.split()[0], 100, spec, EXPIRY, cash_flow=-parts.nov)
    return trade, -parts.nov, value, marks, parts


BOOKS = [(SOLD, loss) for loss in (0.0, 3_929.0, 20_000.0, 60_000.0)] + [
    (BOUGHT, loss) for loss in (0.0, 3_000.0, 5_000.0)
]


@pytest.mark.parametrize(
    ("held_side", "loss"), BOOKS, ids=[f"held_{'credit' if s == SOLD else 'debit'}_{l:g}" for s, l in BOOKS]
)
@pytest.mark.parametrize("new_side", [SOLD, BOUGHT], ids=["new_credit", "new_debit"])
def test_with_an_open_losing_trade_c2_never_leaves_more_free_than_the_broker(tmp_path, held_side, loss, new_side):
    """An open fly marked at a loss (a credit SF, or a debit BF: judge 77's mirror case), then a new SF (credit) or BF
    (debit) at the 14 Oct parts. The broker blocks max(0, scan - NOV) + exposure per trade at today's values and holds
    the cash; C2 must leave exactly that free (the debit's loss is kept above its scan, where the row's parts hold)."""
    held, held_cash, held_value, held_marks, held_parts = _held(held_side, loss)
    the_book = book([held], cash=START + held_cash, marked=START + held_cash + held_value)
    spec = short_fly(22700, 100) if new_side == SOLD else [(k, kind, -s) for k, kind, s in short_fly(22700, 100)]
    new_parts = SF_100 if new_side == SOLD else BF_100
    new = proposal("new", new_parts.what.split()[0], 100, spec, EXPIRY)
    verdict = _room(tmp_path).check(new, the_book, market(22721.95, MIDS | held_marks, EXPIRY, day=DAY))
    c2_free = verdict.numbers["available_after_entry_rs"] - verdict.numbers["needed_rs"]
    broker_cash = START + held_cash - new_parts.nov  # the entry pays or receives the new trade's value
    broker_free = broker_cash - _broker_margin(held_parts, held_value) - _broker_margin(new_parts, new_parts.nov)
    assert c2_free == pytest.approx(broker_free, abs=0.01)  # exact: never looser, and not stricter either
    # Groww at entry (judge 77 addendum 3): no sold-premium credit, the bought legs paid, the held margin still blocked
    bought = sum(units * MIDS[(k, kind)] for (k, kind, s) in spec for units in (65,) if s == BOUGHT)
    groww_free = START + held_cash - _broker_margin(held_parts, held_value) - new_parts.at_entry(1.0) - bought
    at_entry_free = verdict.numbers["free_before_entry_rs"] - verdict.numbers["needed_at_entry_rs"]
    assert at_entry_free == pytest.approx(groww_free, abs=0.01)

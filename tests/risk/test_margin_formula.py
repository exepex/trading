"""Judge 75 (story A14): C2 counts max(0, scan - NOV) + min(0, NOV) + exposure, stresses the scan risk only, refuses a
margin not above 0, and with an open losing trade never leaves more free than a broker that nets the premium."""

from datetime import date

import pytest

from fno.research_engine.structures import BOUGHT, SOLD
from fno.risk.inputs import RiskInputError
from fno.risk.margins import MarginParts, MarginTable, MultiplierMargin
from fno.risk.rules import MarginRoom
from fno.risk.settings import StressedMarginSettings

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


def test_the_stress_factor_grows_the_scan_risk_never_the_premium():
    assert SF_100.stressed(1.45) == pytest.approx(1.45 * 822.25 + 59077.07)
    assert BF_100.stressed(1.45) == pytest.approx(59077.07)  # 1.45 x 831.35 is still below the 6,071 paid
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
    settings = StressedMarginSettings("multiplier", 1.0, "exact input", DAY, 30, None)
    return MarginRoom(MultiplierMargin(MarginTable(tmp_path / "margins.csv", 7), settings), CostsAtMid())


class CostsAtMid:
    """Entry at mid with no charges: the cash flow is minus the position's value."""

    def entry_cash_flow(self, prop, the_market):
        return -sum(units * the_market.quote(c).mid for c, units in prop.signed_units().items())


def _broker_margin(parts: MarginParts, nov_now: float) -> float:
    return max(0.0, parts.scan - nov_now) + parts.exposure  # a broker netting the premium, at the current value


@pytest.mark.parametrize("loss", [0.0, 3_929.0, 20_000.0, 60_000.0])
@pytest.mark.parametrize("new_side", [SOLD, BOUGHT], ids=["new_credit", "new_debit"])
def test_with_an_open_losing_trade_c2_never_leaves_more_free_than_the_broker(tmp_path, loss, new_side):
    """A short fly opened for Rs 6,071 and now marked at a loss, then a new SF (credit) or BF (debit) at the 14 Oct
    parts. The broker blocks max(0, scan - NOV) + exposure per trade at today's values and holds the cash."""
    held_spec = short_fly(22300, 100)
    held_marks = {
        (22300.0, "CE"): (6071.0 + loss) / 65,
        (22300.0, "PE"): 0.0,
        (22400.0, "CE"): 0.0,
        (22200.0, "PE"): 0.0,
    }
    held = open_trade("open", "SF", 100, held_spec, EXPIRY, cash_flow=6071.0)
    nov_open = -(6071.0 + loss)
    the_book = book([held], cash=START + 6071.0, marked=START + 6071.0 + nov_open)
    spec = (
        [(k, kind, -side) for k, kind, side in short_fly(22700, 100)] if new_side == BOUGHT else short_fly(22700, 100)
    )
    new_parts = SF_100 if new_side == SOLD else BF_100
    new = proposal("new", new_parts.what.split()[0], 100, spec, EXPIRY)
    verdict = _room(tmp_path).check(new, the_book, market(22721.95, MIDS | held_marks, EXPIRY, day=DAY))
    c2_free = verdict.numbers["available_after_entry_rs"] - verdict.numbers["needed_rs"]
    broker_cash = START + 6071.0 - new_parts.nov  # the entry pays or receives the new trade's value
    broker_free = broker_cash - _broker_margin(SF_100, nov_open) - _broker_margin(new_parts, new_parts.nov)
    assert c2_free == pytest.approx(broker_free, abs=0.01)  # exact: never looser, and not stricter either

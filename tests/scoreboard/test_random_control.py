"""Story S6 criterion 10: the random control. A fixture snapshot allows exactly two twins of a one-leg trade (its own
strike and one worse), so the percentile is exact: (runs below + ties / 2) / runs, both counts read from the seeded
stream itself."""

import random
from datetime import date

from fno.desk.pricing import DeskLeg
from fno.research_engine.structures import Leg
from fno.risk.open_risk import HeldMaxLoss
from fno.scoreboard.random_control import SEED, RandomControl, RealTrade, Twin, mirrored, window
from tests.scoreboard.matched_builders import CHARGES, EXPIRY, LOT, Snapshots, quote

D1, D2 = date(2026, 11, 2), date(2026, 11, 4)
CALL = DeskLeg("NIFTY-C-25000", EXPIRY, Leg(25000.0, "CE", 1))
TWO = {D1: [quote(25000, "CE", 99, 100), quote(25050, "CE", 79, 80), quote(25000, "PE", 99, 100),
            quote(25050, "PE", 120, 121)],
       D2: [quote(25000, "CE", 130, 131), quote(25050, "CE", 90, 91)]}  # fmt: skip
REAL = RealTrade("XC", (CALL,), LOT, D1, D2, 2210.0, 1.0, 1)  # "XC": no flip, no bucket; risk recomputed (7,615)


def control(quotes, runs=200, **caps) -> RandomControl:
    source = Snapshots(quotes)
    snapshots = lambda day: source.snapshot(day, "s") if day in quotes else None  # noqa: E731
    return RandomControl(snapshots, HeldMaxLoss(CHARGES), CHARGES, caps.get("cap", 10000.0),
                         caps.get("bucket", 30000.0), {"PCS": ["bullish", "short_volatility"]}, runs=runs)  # fmt: skip


def test_the_percentile_is_exact_when_only_two_twins_exist():
    result = control(TWO).control([REAL])
    stream = random.Random(SEED)
    chosen = [stream.choice([25000.0, 25050.0]) for _ in range(200)]
    worse, same = chosen.count(25050.0), chosen.count(25000.0)  # 25,050: net 710 on 6,115 is below 2,210 on 7,615
    assert result["percentile"] == round((worse + same / 2) / 200, 6) and result["missing_twins"] == 0


def test_the_same_records_give_the_same_output():
    assert control(TWO).control([REAL]) == control(TWO).control([REAL])


def test_missing_twins_at_10_percent_are_computable_and_above_are_not():
    unquotable = RealTrade("XC", (CALL,), LOT, D1, date(2026, 11, 5), 1.0, 1.0, 1)  # no snapshot on its exit day
    nine_and_one = [REAL] * 9 + [unquotable]  # every draw of the 10th trade fails: exactly 10% missing
    assert control(TWO, runs=20).control(nine_and_one)["percentile"] is not None
    over = control(TWO, runs=20).control([REAL] * 8 + [unquotable])  # 1 in 9: just over 10%
    assert over["percentile"] is None and "not computable" in over["reason"]


def test_a_twin_that_would_overfill_a_bucket_is_refused():
    luck = control(TWO)
    full = [(D2, Twin(0.0, 10000.0, ("short_volatility",)))] * 3
    assert not luck._bucket_room(Twin(0.0, 10000.0, ("bullish", "short_volatility")), full)
    assert luck._bucket_room(Twin(0.0, 10000.0, ("bearish",)), full)


def test_the_window_widens_to_include_a_real_strike_12_steps_away():
    quotes = [quote(25000 + 50 * i, kind, 10, 11) for i in range(-15, 16) for kind in ("CE", "PE")]
    snapshot = Snapshots({D1: quotes}).snapshot(D1, "s")
    assert 25600.0 in window(snapshot, EXPIRY, 25600.0) and 25650.0 not in window(snapshot, EXPIRY, 25000.0)


def test_a_flip_mirrors_each_leg_about_the_first_strike_and_swaps_calls_and_puts():
    pcs = (DeskLeg("a", EXPIRY, Leg(25000.0, "PE", -1)), DeskLeg("b", EXPIRY, Leg(24900.0, "PE", 1)))  # bull put
    ccs = mirrored(pcs)  # bear call: sell 25,000 CE, buy 25,100 CE
    assert [(leg.leg.strike, leg.leg.kind, leg.leg.side) for leg in ccs] == [(25000.0, "CE", -1), (25100.0, "CE", 1)]
    lc = mirrored((CALL,))
    assert [(leg.leg.strike, leg.leg.kind, leg.leg.side) for leg in lc] == [(25000.0, "PE", 1)]


def test_every_draw_in_the_window_unquotable_at_exit_is_counted_missing_after_the_redraws():
    no_exit_quotes = {D1: TWO[D1], D2: [quote(26000, "CE", 1, 2)]}  # the exit snapshot quotes no strike in the window
    result = control(no_exit_quotes, runs=5).control([REAL])
    assert result["percentile"] is None and result["missing_share"] == 1.0

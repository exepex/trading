"""Protocol section 7, revision 7 (judge 473.1): every vertical in [0, width] at entry, on trigger days and at the
T21 exit; offsetting breaks are caught; an impossible exit is kept out of the decided mean with its failing verticals
clipped as a proxy; skipped trigger days are counted; the naked measurements are never touched."""

from datetime import timedelta

from edge1study.structures import NS, SC2, structure
from edge1study.trade import IMPOSSIBLE, SL2, T21, TAKEN, run_trade
from edge1study.verticals import clipped, proxy_value, valid, verticals

from fno.research_engine.structures import BOUGHT, SOLD, Leg

from .edge1_fakes import DAYS, ENTRY, EXIT, cycle, flat_prices, panel, terms

CONDOR = [Leg(23400.0, "CE", SOLD), Leg(22600.0, "PE", SOLD), Leg(23600.0, "CE", BOUGHT), Leg(22400.0, "PE", BOUGHT)]


def run(code, exit_rule, day_prices=None, capped=True):
    return run_trade(structure(code), panel(day_prices or {}), cycle(), terms(65, 1.0), exit_rule, DAYS,
                     lambda expiry: 23000.0, capped)  # fmt: skip


def test_each_sold_leg_pairs_with_the_bought_leg_of_its_type():
    assert verticals(CONDOR) == [(0, 2, 200.0), (1, 3, 200.0)]


def test_offsetting_breaks_are_caught_and_clipped_into_the_width():
    prices = [50.0, 330.0, 70.0, 100.0]  # call vertical -20, put vertical 230 > 200: the total (210) looks possible
    assert not valid(CONDOR, prices)
    assert clipped(CONDOR, prices) == [50.0, 330.0, 50.0, 130.0]
    assert valid(CONDOR, clipped(CONDOR, prices))


def broken(base, day_prices, offset=True):
    """A put vertical worth its width plus 50 and, with `offset`, a call vertical below 0 by the same amount."""
    sold = {leg.kind: leg.contract for leg in base.legs if not leg.bought}
    bought = {leg.kind: leg.contract for leg in base.legs if leg.bought}
    prices = dict(day_prices)
    prices[sold["PE"]] = prices[bought["PE"]] + base.width + 50.0
    if offset:
        prices[bought["CE"]] = prices[sold["CE"]] + 50.0
    return prices


def test_an_impossible_t21_exit_is_kept_flagged_and_its_proxy_clipped():
    base = run(SC2, T21)
    offsetting = run(SC2, T21, {EXIT: (23000.0, broken(base, flat_prices(23000.0)), set())})
    assert offsetting.impossible_exit and offsetting.incomplete_exit  # its total alone would have passed
    trade = run(SC2, T21, {EXIT: (23000.0, broken(base, flat_prices(23000.0), offset=False), set())})
    assert trade.status == TAKEN and trade.impossible_exit and trade.incomplete_exit
    assert trade.raw_net is not None and trade.raw_net < trade.net  # the raw close loses beyond the width
    worst = -(base.width - base.credit) * 65 - trade.charges - trade.pads  # a clipped exit cannot lose beyond the width
    assert trade.net >= worst - 1e-6


def test_trigger_days_with_impossible_prices_are_skipped_and_counted():
    base = run(SC2, SL2)
    days = {ENTRY + timedelta(days=d): (23000.0, broken(base, flat_prices(23000.0)), set()) for d in (2, 3)}
    trade = run(SC2, SL2, days)
    assert trade.exit_how == "planned" and trade.skipped_days == 2


def test_no_entry_on_impossible_prices():
    prices = flat_prices(23000.0)
    for k in range(21000, 25100, 100):  # every put vertical inverted: lower strikes dearer than higher ones
        prices[(float(k), "PE")] = 25_000.0 - k
    assert run(SC2, T21, {ENTRY: (23000.0, prices, set())}).status == IMPOSSIBLE


def test_the_naked_measurements_are_never_touched():
    base = run(NS, T21, capped=False)
    wild = {**flat_prices(23000.0), base.legs[0].contract: 5_000.0}
    trade = run(NS, T21, {EXIT: (23000.0, wild, set())}, capped=False)
    assert not trade.impossible_exit and trade.raw_net is None and trade.skipped_days == 0


def test_the_proxy_also_keeps_the_position_inside_its_bounds():
    prices = [250.0, 330.0, 50.0, 100.0]  # call vertical 200 (valid alone), put vertical 230: clipped to 200
    assert not valid(CONDOR, [250.0, 300.0, 50.0, 100.0])  # both verticals at 200: the condor's total breaks its bound
    assert proxy_value(CONDOR, prices) == -200.0  # worth at most one width, never two

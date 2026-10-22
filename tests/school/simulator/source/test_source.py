"""The historical road source and catalogue (MS-SIM-c)."""

from dataclasses import replace
from datetime import date

import pytest

from fno.research_data.calendar import CsvSessionCalendar
from fno.school.constants import ClosureReason, OptionKind, RoadCode
from fno.school.contracts.roads import ROADS_BY_CODE
from fno.school.contracts.snapshot import ContractKey, SnapshotUnavailable
from fno.school.simulator.constants import PracticeRefusal
from fno.school.simulator.source.catalogue import HistoricalRoadCatalogue
from fno.school.simulator.source.quotes import SIZE_GATE_WAIVED
from fno.school.simulator.source.snapshots import HistoricalRoadSource
from fno.school.simulator.spreads.model import Scenario, SpreadModel
from fno.school.simulator.terms import DatedTerms
from fno.school.simulator.windows import PracticeWindows
from tests.school.contracts.conformance import check_road_catalogue, check_snapshot_source
from tests.school.simulator.source import builders as sb

NIFTY_M, NIFTY_W = ROADS_BY_CODE[RoadCode.NIFTY_MONTHLY], ROADS_BY_CODE[RoadCode.NIFTY_WEEKLY]
CALL, PUT = OptionKind.CALL, OptionKind.PUT


def catalogue(chain=None, windows=None):
    chain = chain or sb.DictChain(sb.chain("NIFTY"), sb.chain("BANKNIFTY"))
    return HistoricalRoadCatalogue(sb.CALENDAR, chain, sb.TERMS, windows or PracticeWindows())


def open_day(road=NIFTY_M, chain=None):
    day = next(d for d in catalogue(chain).day(sb.SESSION) if d.road.code == road.code)
    assert day.status.open, day.status
    return day


def source(model=None, scenario=Scenario.MEDIAN, chain=None, windows=None):
    model = model or sb.full_model(RoadCode.NIFTY_MONTHLY)
    chain = chain or sb.DictChain(sb.chain("NIFTY"), sb.chain("BANKNIFTY"))
    return HistoricalRoadSource(chain, model, scenario, windows or PracticeWindows())


# ---- the catalogue ---------------------------------------------------------------------------------------------------


def test_the_catalogue_and_source_pass_the_pilots_conformance_checks():
    cat = catalogue()
    check_road_catalogue(cat, sb.SESSION, sb.HOLIDAY)
    closed = next(d for d in cat.day(sb.SESSION) if not d.status.open)
    check_snapshot_source(source(), open_day(), closed)


def test_an_open_road_has_two_expiries_a_dated_lot_and_each_expiry_its_own_step():
    day = open_day()
    assert (
        day.expiries == sb.MONTHLIES and day.lot.units == 50 and day.strike_steps == dict.fromkeys(sb.MONTHLIES, 100.0)
    )
    weekly = open_day(NIFTY_W)
    assert weekly.expiries == sb.WEEKLIES


def test_only_the_two_nearest_expiries_not_yet_expired_are_recorded():
    expired, third = date(2022, 2, 24), date(2022, 5, 26)
    extra = sb.rows((expired, third), True)
    base = sb.chain("NIFTY")
    chain = sb.DictChain(replace(base, rows=base.rows + tuple(extra)))
    assert open_day(chain=chain).expiries == sb.MONTHLIES


def test_the_lot_is_the_one_in_force_on_that_date():
    before = sb.chain(
        "NIFTY", date(2021, 6, 1)
    )  # circular: 75 until the July 2021 expiry; the chain's expiries are 2022's
    assert sb.TERMS.lot(before, date(2021, 6, 24)).units == 75


def test_roads_outside_the_data_spend_window_are_closed_with_the_detail():
    days = {d.road.code: d for d in catalogue().day(sb.SESSION)}
    for code in (RoadCode.FINNIFTY_MONTHLY, RoadCode.MIDCPNIFTY_MONTHLY):
        status = days[code].status
        assert status.closed_by is ClosureReason.CAPTURE_MISSING and PracticeRefusal.NOT_IN_DATA_SPEND in status.detail


def test_a_session_after_the_window_is_closed_even_with_data():
    late = date(2026, 10, 13)
    calendar = CsvSessionCalendar("date,kind,description,source_url\n2026-01-26,holiday,test,https://example.test/c\n")
    cat = HistoricalRoadCatalogue(calendar, sb.DictChain(sb.chain("NIFTY", late)), sb.TERMS, PracticeWindows())
    day = next(d for d in cat.day(late) if d.road.code is RoadCode.NIFTY_MONTHLY)
    assert not day.status.open and PracticeRefusal.NOT_IN_DATA_SPEND in day.status.detail


def test_no_chain_fewer_than_two_expiries_or_no_lot_close_the_road_with_one_reason_each():
    no_chain = {d.road.code: d for d in catalogue(sb.DictChain()).day(sb.SESSION)}
    assert no_chain[RoadCode.NIFTY_MONTHLY].status.closed_by is ClosureReason.CAPTURE_MISSING
    one = sb.chain("NIFTY")
    one = replace(one, rows=tuple(r for r in one.rows if r.expiry != sb.MONTHLIES[1]))
    assert open_day_status(sb.DictChain(one)) is ClosureReason.EXPIRY_MISMATCH
    no_index = replace(sb.chain("NIFTY"), index_close=None)
    assert open_day_status(sb.DictChain(no_index)) is ClosureReason.CAPTURE_MISSING


def open_day_status(chain):
    return next(d for d in catalogue(chain).day(sb.SESSION) if d.road.code is RoadCode.NIFTY_MONTHLY).status.closed_by


def test_a_lot_that_neither_the_file_nor_the_schedule_states_closes_the_road():
    terms = DatedTerms(lambda underlying, expiry: None, sb.TERMS.charges_on)
    cat = HistoricalRoadCatalogue(sb.CALENDAR, sb.DictChain(sb.chain("NIFTY")), terms, PracticeWindows())
    day = next(d for d in cat.day(sb.SESSION) if d.road.code is RoadCode.NIFTY_MONTHLY)
    assert day.status.closed_by is ClosureReason.LOT_MISMATCH


def test_two_different_lots_close_the_road():
    two = replace(sb.chain("NIFTY"), lots={sb.MONTHLIES[0]: 50, sb.MONTHLIES[1]: 75})
    assert open_day_status(sb.DictChain(two)) is ClosureReason.LOT_MISMATCH


# ---- the snapshot --------------------------------------------------------------------------------------------------


def key(strike, kind=CALL, expiry=sb.MONTHLIES[0]):
    return ContractKey(expiry, strike, kind)


def test_the_quote_is_the_close_less_and_plus_the_half_spread_rounded_outward_to_a_tick():
    snap = source().for_road(open_day())
    quote, close = snap.quotes[key(sb.SPOT)], sb.close_of(sb.SPOT, CALL)
    assert quote.last == close and quote.valid and quote.two_sided
    half = close * 0.01
    assert quote.bid <= close - half + 1e-9 < quote.bid + 0.05 + 1e-9 and quote.ask >= close + half - 1e-9
    assert round(quote.bid / 0.05, 6) == round(quote.bid / 0.05) and round(quote.ask / 0.05, 6) == round(
        quote.ask / 0.05
    )


def test_both_sizes_are_the_waiver_switch_and_nothing_else():
    snap = source().for_road(open_day())
    sizes = {s for q in snap.quotes.values() if q.valid for s in (q.bid_qty, q.ask_qty)}
    assert sizes == {SIZE_GATE_WAIVED}


def rising_model() -> SpreadModel:
    """Every bucket's 30 sessions run from a 0.1% to a 3% half-spread, so the three scenarios differ."""
    full = sb.full_model(RoadCode.NIFTY_MONTHLY)
    return SpreadModel({b: {d: 0.001 * (i + 1) for i, d in enumerate(days)} for b, days in full.by_session.items()})


def test_a_wider_scenario_gives_a_wider_quote():
    gaps = {}
    for scenario in Scenario:
        quote = source(rising_model(), scenario).for_road(open_day()).quotes[key(sb.SPOT)]
        gaps[scenario] = quote.ask - quote.bid
    assert gaps[Scenario.MEDIAN] < gaps[Scenario.P75] < gaps[Scenario.P95]


def test_a_leg_that_did_not_trade_has_no_quote_and_one_that_traded_once_has():
    rows = [r if r.strike != sb.SPOT else replace(r, volume=0) for r in sb.chain("NIFTY").rows]
    rows = [replace(r, volume=1) if r.strike == sb.SPOT + 100 and r.kind is CALL else r for r in rows]
    chain = sb.DictChain(replace(sb.chain("NIFTY"), rows=tuple(rows)))
    snap, coverage = source(chain=chain).build(open_day(chain=chain))
    assert not snap.quotes[key(sb.SPOT)].valid and not snap.quotes[key(sb.SPOT, PUT)].valid
    assert snap.quotes[key(sb.SPOT + 100)].two_sided
    assert coverage.untraded == 4  # two strikes' call and put on... both monthly expiries


def test_a_planted_impossible_vertical_leaves_both_legs_without_a_quote():
    """EDGE1's example: a wide call spread whose far leg closes dearer than the near one."""
    rows = [replace(r, close=392.0) if (r.strike, r.kind, r.expiry) == (sb.SPOT + 100, CALL, sb.MONTHLIES[0]) else r
            for r in sb.chain("NIFTY").rows]  # fmt: skip
    chain = sb.DictChain(replace(sb.chain("NIFTY"), rows=tuple(rows)))
    snap, coverage = source(chain=chain).build(open_day(chain=chain))
    assert not snap.quotes[key(sb.SPOT + 100)].valid and coverage.impossible >= 1
    assert snap.quotes[key(sb.SPOT + 200, CALL, sb.MONTHLIES[1])].two_sided  # the other expiry is untouched


def test_an_insufficient_bucket_gives_no_quote_and_is_counted_never_a_zero_spread():
    snap, coverage = source(SpreadModel({})).build(open_day())
    assert not any(q.valid for q in snap.quotes.values())
    assert coverage.priced == 0 and sum(coverage.insufficient.values()) == coverage.legs


def test_a_close_that_leaves_no_bid_is_unsellable():
    rows = [
        replace(r, close=0.05) if (r.strike, r.kind) == (sb.SPOT + 500, CALL) else r for r in sb.chain("NIFTY").rows
    ]
    chain = sb.DictChain(replace(sb.chain("NIFTY"), rows=tuple(rows)))
    quote = source(chain=chain).for_road(open_day(chain=chain)).quotes[key(sb.SPOT + 500)]
    assert quote.bid is None and not quote.two_sided


def test_only_the_sessions_own_chain_is_read():
    chain = sb.DictChain(sb.chain("NIFTY"), sb.chain("NIFTY", date(2022, 3, 8)), sb.chain("NIFTY", date(2022, 3, 9)))
    day = open_day(chain=chain)
    chain.asked.clear()
    source(chain=chain).for_road(day)
    assert chain.asked == [("NIFTY", sb.SESSION)]


def test_a_hand_built_open_road_day_outside_the_window_is_refused_at_the_data():
    late = replace(open_day(), session=date(2026, 10, 20))
    with pytest.raises(SnapshotUnavailable) as raised:
        source(chain=sb.DictChain(sb.chain("NIFTY", late.session))).for_road(late)
    assert raised.value.reason is ClosureReason.CAPTURE_MISSING and PracticeRefusal.NOT_IN_DATA_SPEND in str(
        raised.value
    )


def test_a_weekly_expiring_on_the_session_is_not_recorded_but_a_monthly_is():
    weekly_today = (sb.SESSION, sb.WEEKLIES[1], date(2022, 3, 24))
    base = sb.chain("NIFTY")
    rows = tuple(r for r in base.rows if r.monthly) + tuple(sb.rows(weekly_today, False))
    day = open_day(NIFTY_W, sb.DictChain(replace(base, rows=rows)))
    assert day.expiries == (sb.WEEKLIES[1], date(2022, 3, 24))
    monthly_today = tuple(sb.rows((sb.SESSION, sb.MONTHLIES[0]), True))
    only = replace(base, rows=monthly_today)
    assert open_day(NIFTY_M, sb.DictChain(only)).expiries == (sb.SESSION, sb.MONTHLIES[0])


def test_the_digest_covers_the_close_even_when_the_quote_is_unchanged():
    day = open_day()
    wide = sb.full_model(RoadCode.NIFTY_MONTHLY, scenario_gap=0.5)
    base = sb.chain("NIFTY")
    bumped = tuple(
        replace(r, close=r.close + 0.01) if (r.strike, r.kind, r.expiry) == (sb.SPOT, CALL, sb.MONTHLIES[0]) else r
        for r in base.rows
    )
    a = source(wide, chain=sb.DictChain(base)).for_road(day)
    b = source(wide, chain=sb.DictChain(replace(base, rows=bumped))).for_road(day)
    assert a.quotes[key(sb.SPOT)].bid == b.quotes[key(sb.SPOT)].bid and a.sha256 != b.sha256


def test_a_contract_listed_twice_counts_once():
    base = sb.chain("NIFTY")
    chain = sb.DictChain(replace(base, rows=base.rows + base.rows[:3]))
    _, coverage = source(chain=chain).build(open_day(chain=chain))
    assert coverage.legs == len([r for r in base.rows if r.expiry in sb.MONTHLIES])


def test_a_priced_leg_with_no_bid_is_counted_unsellable_not_priced():
    rows = tuple(
        replace(r, close=0.05) if (r.strike, r.kind) == (sb.SPOT + 500, CALL) else r for r in sb.chain("NIFTY").rows
    )
    chain = sb.DictChain(replace(sb.chain("NIFTY"), rows=rows))
    _, coverage = source(chain=chain).build(open_day(chain=chain))
    assert coverage.unsellable == 2 and coverage.unpriced >= 2  # both monthly expiries


def test_the_same_day_gives_the_same_bytes_and_a_changed_close_changes_them():
    day = open_day()
    assert source().for_road(day).sha256 == source().for_road(day).sha256
    rows = tuple(replace(r, close=r.close + 1) if r.strike == sb.SPOT else r for r in sb.chain("NIFTY").rows)
    other = sb.DictChain(replace(sb.chain("NIFTY"), rows=rows))
    assert source(chain=other).for_road(day).sha256 != source().for_road(day).sha256


def test_a_closed_road_and_a_vanished_chain_are_unavailable_with_a_reason():
    closed = next(d for d in catalogue().day(sb.SESSION) if not d.status.open)
    with pytest.raises(SnapshotUnavailable) as raised:
        source().for_road(closed)
    assert raised.value.reason is closed.status.closed_by
    with pytest.raises(SnapshotUnavailable) as gone:
        source(chain=sb.DictChain()).for_road(open_day())
    assert gone.value.reason is ClosureReason.CAPTURE_MISSING


# ---- dated costs in the pilot's own cost model -------------------------------------------------------------------


def credit_spread_max_loss(session: date) -> float:
    from fno.research_engine.cycle_costs import PAD, CycleTerms, PositionCosts
    from fno.research_engine.structures import BOUGHT, SOLD, Leg

    costs = PositionCosts(CycleTerms(lot=50, charges=sb.TERMS.charges(session), pad=PAD))
    legs = [Leg(17000.0, "PE", SOLD), Leg(16900.0, "PE", BOUGHT)]
    return costs.max_loss(legs, [80.0, 50.0])


def test_a_2022_trade_is_charged_the_2022_stt_and_a_2026_trade_the_2026_one():
    assert credit_spread_max_loss(date(2022, 3, 7)) < credit_spread_max_loss(date(2026, 5, 4))
    assert credit_spread_max_loss(date(2023, 3, 31)) < credit_spread_max_loss(
        date(2023, 4, 3)
    )  # both sides of a change

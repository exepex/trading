"""Part c's evidence (story MS-INS): each term gathered through the ports from a model-priced put spread, and
"not testable" whenever an input is missing."""

import math
from dataclasses import replace
from datetime import date

import pytest

from fno.school.constants import ExitReason, RoadCode
from fno.school.contracts.accounts import SettlementPrice
from fno.school.contracts.decisions import Decision
from fno.school.fakes import FakeFills, FakeSettlementSource
from fno.school.instructor.attribution.attribute import attribute
from fno.school.instructor.attribution.points import years_left
from fno.school.instructor.causes.evidence import EvidenceBuilder
from fno.school.instructor.fakes import FakeCardReplay, FakeEventCalendar, FakeSnapshotArchive, FakeStopSource
from tests.school.instructor.attribution.fixtures import EXPIRY, SHORT
from tests.school.instructor.builders import AFTER_EXPIRY, RULES
from tests.school.instructor.causes.paths import ENTRY_DAY, EXIT_DAY, market_snapshots, spread_path

MONTHLIES = (RoadCode.NIFTY_MONTHLY, RoadCode.BANKNIFTY_MONTHLY, RoadCode.FINNIFTY_MONTHLY, RoadCode.MIDCPNIFTY_MONTHLY)


def builder(archive=None, events=None, stops=None, replay=None, settlement: float | None = None) -> EvidenceBuilder:
    prices = {("BANKNIFTY", EXPIRY): SettlementPrice(settlement, "ab" * 32)} if settlement is not None else {}
    return EvidenceBuilder(archive or FakeSnapshotArchive(), events or FakeEventCalendar(), stops or FakeStopSource(),
                           replay or FakeCardReplay(), FakeFills(FakeSettlementSource(prices)), 0.0)  # fmt: skip


def gathered(held=None, **ports):
    held = held or spread_path()
    return builder(**ports).build(held, attribute(held, 0.0, RULES), None, AFTER_EXPIRY)


def test_the_move_is_measured_against_the_entry_atm_volatility():
    entry_at = spread_path().snapshots[0].finished_at
    exit_at = spread_path().snapshots[-1].finished_at
    held_years = years_left(entry_at, EXPIRY) - years_left(exit_at, EXPIRY)
    assert gathered().z == pytest.approx(math.log(980 / 1000) / (0.20 * math.sqrt(held_years)), rel=1e-6)


def test_a_credit_put_spread_is_short_volatility_not_long_premium_and_not_directional_at_this_size():
    stance = gathered().stance
    assert stance.short_volatility and not stance.long_volatility and not stance.long_premium
    assert not stance.directional  # |delta| x F x 1% = 143 < 20% of the Rs 3,000 maximum loss


def test_the_market_moves_of_every_measurable_underlying():
    archive = FakeSnapshotArchive(market_snapshots(dict.fromkeys(MONTHLIES, 0.05)))
    moves = gathered(archive=archive).market
    assert len(moves) == 4 and all(z > 2 for z in moves)
    assert gathered(archive=FakeSnapshotArchive(market_snapshots({RoadCode.NIFTY_MONTHLY: 0.05}))).market[0] > 2


@pytest.mark.parametrize("known_on, expected", [(ENTRY_DAY, True), (date(2026, 11, 3), False)])
def test_a_scheduled_event_counts_only_when_known_at_entry(known_on, expected):
    assert gathered(events=FakeEventCalendar({EXIT_DAY: known_on})).event_in_window is expected


def test_the_stop_is_the_cards_multiple_of_the_entry_credit():
    held = spread_path()
    assert gathered(held, stops=FakeStopSource({"CS1@1": 2.0})).stop_rs == pytest.approx(2 * held.outcome.entry.cash)
    assert gathered(held).stop_rs is None


def test_holding_to_expiry_is_valued_at_settlement_and_waits_for_it():
    held = spread_path()
    assert gathered(held).hold_net is None
    hold = gathered(held, settlement=985.0).hold_net
    assert hold == pytest.approx(held.outcome.entry.cash - 15.0 * 30)  # the short 1000 put settles at 15
    assert gathered(spread_path(reason=ExitReason.SESSIONS_HELD), settlement=985.0).hold_net is None


def test_the_replay_mismatch_and_the_unreplayable():
    held = spread_path()
    other = Decision("CS1@1", held.entry.road, held.entry.session, "no_trade", "rule_not_fired")
    assert gathered(held).replay_matches is True
    assert gathered(held, replay=FakeCardReplay({"CS1@1": other})).replay_matches is False
    assert gathered(held, replay=FakeCardReplay({"CS1@1": None})).replay_matches is None


def test_a_fill_away_from_the_touch_or_at_an_impossible_price_is_a_data_fault():
    held = spread_path()
    assert gathered(held).data_fault is False
    legs = (
        replace(held.outcome.entry.legs[0], price=held.outcome.entry.legs[0].price - 0.5),
    ) + held.outcome.entry.legs[1:]
    off = replace(held, outcome=replace(held.outcome, entry=replace(held.outcome.entry, legs=legs)))
    assert builder().build(off, attribute(held, 0.0, RULES), None, AFTER_EXPIRY).data_fault is True
    first = held.snapshots[0]
    impossible = replace(first, quotes={**first.quotes, SHORT: replace(first.quote(SHORT), bid=1500.0, ask=1501.0)})
    assert gathered(replace(held, snapshots=(impossible,) + held.snapshots[1:])).data_fault is True


def test_the_noise_band_and_its_absence():
    mean, sd = gathered().noise
    assert sd > 0 and math.isfinite(mean)
    assert gathered(replace(spread_path(), entry=None)).noise is None  # no entry decision: no terms


def test_a_settled_path_measures_its_move_to_the_settlement_price():
    held = spread_path(settlement=985.0)
    ev = gathered(held, settlement=985.0)
    assert ev.z < 0 and ev.hold_net is None  # settled at expiry: nothing left to hold


def test_a_missing_attribution_is_not_a_data_fault():
    """No mid at the exit leaves the Greek causes untestable; it is not "bad price or data" (self-review)."""
    held = spread_path()
    assert gathered(held).data_fault is False
    assert builder().build(held, None, None, AFTER_EXPIRY).data_fault is False


def test_a_path_without_an_entry_or_snapshots_gathers_nothing_and_does_not_crash():
    held = spread_path()
    no_entry = builder().build(replace(held, entry=None), None, None, AFTER_EXPIRY)
    assert (no_entry.z, no_entry.stance, no_entry.hold_net, no_entry.replay_matches) == (None, None, None, None)
    empty = builder().build(replace(held, snapshots=(), entry=None), None, None, AFTER_EXPIRY)
    assert (empty.z, empty.market, empty.noise) == (None, (), None)


def test_the_market_move_uses_an_expiry_alive_over_the_window_and_the_clock_time_held():
    shots = market_snapshots({RoadCode.NIFTY_MONTHLY: 0.01})
    start, end = shots[(RoadCode.NIFTY_MONTHLY, ENTRY_DAY)], shots[(RoadCode.NIFTY_MONTHLY, EXIT_DAY)]
    dying = date(2026, 11, 3)  # expires inside the window: its volatility must not be used
    shots[(RoadCode.NIFTY_MONTHLY, ENTRY_DAY)] = replace(start, expiries=(dying, EXPIRY))
    (z,) = gathered(archive=FakeSnapshotArchive(shots)).market
    held = (end.finished_at - start.finished_at).total_seconds() / 60 / (365 * 1440)
    assert z == pytest.approx(math.log(1.01) / (0.20 * math.sqrt(held)), rel=1e-6)
    only_dying = {**shots, (RoadCode.NIFTY_MONTHLY, ENTRY_DAY): replace(start, expiries=(dying,))}
    assert gathered(archive=FakeSnapshotArchive(only_dying)).market == ()

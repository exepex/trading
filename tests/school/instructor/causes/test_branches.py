"""Part c's branches judge 510 could break with every test green (round 2): one test per branch, each failing when
its branch is broken."""

from dataclasses import replace
from datetime import date

import pytest

from fno.school.constants import ExitReason, OptionKind
from fno.school.contracts.snapshot import ContractKey, SlotQuote
from fno.school.instructor.attribution.attribute import attribute
from fno.school.instructor.attribution.greeks import price
from fno.school.instructor.attribution.points import snapshot_point, years_left
from fno.school.instructor.causes import terms
from fno.school.instructor.causes.classify import causes_of
from fno.school.instructor.causes.rules import verdicts
from fno.school.instructor.contracts import Cause
from tests.school.instructor.attribution.fixtures import EXPIRY, SHORT, model_snapshot, path
from tests.school.instructor.builders import AFTER_EXPIRY, RULES
from tests.school.instructor.causes.evidence_builders import FLAT, evidence, with_parts
from tests.school.instructor.causes.paths import ENTRY_DAY, entry_record
from tests.school.instructor.causes.test_evidence import builder

DIRECTIONAL = replace(FLAT, directional=True)
LONG_PREMIUM = replace(FLAT, long_premium=True)


@pytest.mark.parametrize("z, fires", [(1.645, True), (-1.645, True), (1.6451, False)])
def test_cause_2_holds_up_to_and_including_the_range_edge(z, fires):
    assert verdicts(with_parts(evidence(stance=DIRECTIONAL, z=z), delta=-1.0))[Cause.WRONG_DIRECTION] is fires


def test_a_winning_debit_never_reads_time_decay_earned():
    win = evidence(net=500.0, gross=600.0)
    assert verdicts(with_parts(replace(win, stance=FLAT), theta=200.0))[Cause.TIME_DECAY] is True
    assert verdicts(with_parts(replace(win, stance=LONG_PREMIUM), theta=200.0))[Cause.TIME_DECAY] is False


def test_a_winner_closed_by_its_stop_is_never_a_whipsaw():
    win = evidence(net=500.0, gross=600.0, exit_reason=ExitReason.LOSS_LIMIT, hold_net=5000.0)
    assert verdicts(win)[Cause.EXIT_WHIPSAW] is False
    assert verdicts(replace(win, exit_reason=ExitReason.PROFIT_TARGET))[Cause.EXIT_WHIPSAW] is True


def test_costs_rank_before_noise_in_the_tail():
    both = evidence(gross=0.0, noise=(-920.0, 10.0))  # the mid-to-mid P&L is -920: inside the band
    assert causes_of(both)[:2] == (Cause.COSTS_ATE_EDGE, (Cause.NORMAL_NOISE,))


def test_the_directional_boundary_is_inclusive(monkeypatch):
    """With a binary-exact share (0.25), a maximum loss of exactly 4 x the 1% dollar delta is directional."""
    monkeypatch.setattr(terms, "DIRECTIONAL_SHARE", 0.25)
    shot = model_snapshot(ENTRY_DAY, 1000.0, 0.20)
    units = {SHORT: -30}
    point = snapshot_point(shot, tuple(units), 0.0)
    g = terms.greeks(point.forwards[EXPIRY], SHORT.strike, "PE", point.years[EXPIRY], 0.0, point.sigmas[SHORT])
    one_percent = abs(-30 * g.delta * point.forwards[EXPIRY]) * 0.01
    assert terms.stance(point, units, 0.0, one_percent * 4, 100.0).directional is True
    assert terms.stance(point, units, 0.0, one_percent * 4 * 1.0001, 100.0).directional is False


def test_the_noise_band_is_centred_by_the_lognormal_drift():
    """A long ATM call held to expiry at its own volatility: the band's mean P&L is about 0, because the forward is a
    martingale. Without the -s^2/2 drift the forward's mean rises by F x (e^(s^2/2) - 1), about Rs 1.2 on F = 1000
    (s = 0.20 x sqrt(0.0576)), and the call's mean P&L moves up by about half of that."""
    shot = model_snapshot(ENTRY_DAY, 1000.0, 0.20)
    call = ContractKey(EXPIRY, 1000.0, OptionKind.CALL)
    point = snapshot_point(shot, (call,), 0.0)
    held = years_left(shot.finished_at, EXPIRY)
    mean, sd = terms.noise_band(point, {call: 1}, 0.20, held, {EXPIRY: 0.0}, 0.0)
    assert abs(mean) < 0.3 and sd > 10


def test_the_atm_volatility_is_read_at_the_strike_nearest_the_forward():
    shot = model_snapshot(ENTRY_DAY, 1000.0, 0.20)
    years = years_left(shot.finished_at, EXPIRY)
    skewed = dict(shot.quotes)
    for kind in OptionKind:  # the lowest strike's quotes at 40% volatility
        mid = price(1000.0, 900.0, kind.value, years, 0.0, 0.40)
        skewed[ContractKey(EXPIRY, 900.0, kind)] = SlotQuote(mid - 0.05, mid + 0.05, 1000, 1000, mid, True)
    assert terms.atm_volatility(replace(shot, quotes=skewed), EXPIRY, 1000.0, 0.0) == pytest.approx(0.20, abs=1e-6)


def test_an_impossible_price_alone_is_a_data_fault_with_fills_at_the_touch():
    first = model_snapshot(ENTRY_DAY, 1000.0, 0.20)
    impossible = replace(first, quotes={**first.quotes, SHORT: replace(first.quote(SHORT), bid=1500.0, ask=1501.0)})
    held = replace(path((impossible, model_snapshot(date(2026, 11, 4), 980.0, 0.22))), entry=entry_record())
    assert held.outcome.entry.legs[0].price == 1500.0  # filled at that touch: the off-touch half sees nothing
    assert builder().build(held, attribute(held, 0.0, RULES), None, AFTER_EXPIRY).data_fault is True

"""The cards' exit rules (story MS-P1e): profit and loss at the mid of the slot, time rules, expiry, and the rule that
a price which cannot be judged never fires."""

from dataclasses import replace
from datetime import timedelta

import pytest

from fno.school.constants import ExitReason
from fno.school.contracts.snapshot import SlotQuote
from fno.school.drivers.exits import ExitPlan, net_if_closed
from tests.school.drivers import builders as b


def opened_ps4():
    road_day, snapshot = b.scene()
    driver = b.drivers()["PS4"]
    return driver, b.position_from(driver.decide(road_day, snapshot, (), ()), driver)


def repriced(snapshot, factor):
    """The same chain with every mid moved by `factor` (a market that has moved against or for a seller)."""
    quotes = {
        key: q if q.bid is None else SlotQuote(round(q.bid * factor, 2), round(q.ask * factor, 2), q.bid_qty,
                                               q.ask_qty, q.last, True)
        for key, q in snapshot.quotes.items()
    }  # fmt: skip
    return replace(snapshot, quotes=quotes)


def on_day(days: int):
    """The entry-day chain read `days` calendar days later: prices unchanged, so only the time rules can fire."""
    return replace(b.scene()[1], session=b.SESSION + timedelta(days=days))


def test_a_credit_position_closes_at_half_its_credit_and_not_just_short_of_it():
    driver, position = opened_ps4()
    _, snapshot = b.scene()
    target = 0.5 * abs(position.entry_net)
    low, high = 0.0, 1.0  # profit falls as prices rise: bisect the price level where it equals the target
    for _ in range(60):
        mid = (low + high) / 2
        low, high = (mid, high) if net_if_closed(position, repriced(snapshot, mid)) >= target else (low, mid)
    reached, short = repriced(snapshot, low - 1e-4), repriced(snapshot, high + 1e-3)
    assert driver.review_exit(position, reached, ()) == ExitReason.PROFIT_TARGET
    assert driver.review_exit(position, short, ()) is None


def test_a_loss_of_twice_the_credit_closes_a_ws1_position_only_at_its_own_multiple():
    ws1 = b.drivers()["WS1"]
    road_day, snapshot = b.scene(days=(3,), vol=0.4, code=ws1.card.roads[0], spot=25_000.0, step=50.0, lot=75)
    position = b.position_from(ws1.decide(road_day, snapshot, (), ()), ws1)
    losing = [f for f in (1.5, 2.0, 3.0, 4.0, 6.0) if ws1.review_exit(position, repriced(snapshot, f), ()) is not None]
    assert losing and ws1.review_exit(position, repriced(snapshot, 1.0), ()) is None
    first = ws1.review_exit(position, repriced(snapshot, losing[0]), ())
    assert first == ExitReason.LOSS_LIMIT
    profit = net_if_closed(position, repriced(snapshot, losing[0]))
    assert -profit >= 1.5 * abs(position.entry_net)


def test_ps_positions_close_after_21_days_held_and_at_expiry():
    driver, position = opened_ps4()
    assert driver.review_exit(position, on_day(20), ()) is None
    assert driver.review_exit(position, on_day(21), ()) == ExitReason.DAYS_HELD
    assert driver.review_exit(position, on_day(30), ()) == ExitReason.EXPIRY  # expiry beats every other rule


def test_cs1_closes_after_ten_sessions():
    cs1 = b.drivers()["CS1"]
    road_day, snapshot = b.scene()
    position = b.position_from(cs1.decide(road_day, snapshot, b.history([b.SPOT - 1] * 20), ()), cs1)
    assert cs1.review_exit(position, on_day(11), ()) is None  # 9 sessions after Monday 2 Nov (weekdays only)
    assert cs1.review_exit(position, on_day(14), ()) == ExitReason.SESSIONS_HELD  # Monday 16 Nov: 10 sessions


def test_edge1s_t21_exit_fires_on_the_last_session_with_21_days_to_expiry():
    ps5 = b.drivers()["PS5"]
    road_day, snapshot = b.scene(days=(45, 75))
    position = b.position_from(ps5.decide(road_day, snapshot, (), ()), ps5)
    # expiry is 45 days after the entry Monday = Thursday 17 Dec; 21 days before it is Thursday 26 Nov
    wednesday, thursday = b.SESSION + timedelta(days=23), b.SESSION + timedelta(days=24)
    for session, expected in ((wednesday, None), (thursday, ExitReason.DAYS_BEFORE_EXPIRY)):
        _, snap = b.scene(session=session, days=(45 - (session - b.SESSION).days, 75 - (session - b.SESSION).days))
        assert ps5.review_exit(position, snap, ()) == expected, session


def test_dr1_closes_when_spot_is_back_through_the_window_mean():
    dr1 = b.drivers()["DR1"]
    road_day, snapshot = b.scene()
    position = b.position_from(dr1.decide(road_day, snapshot, b.history([b.SPOT - 500] * 19 + [b.SPOT]), ()), dr1)
    mean_history = b.history([b.SPOT] * 20, b.SESSION + timedelta(days=1))
    above = on_day(1)
    _, below_spot = b.scene(spot=b.SPOT - 1, session=b.SESSION + timedelta(days=1), days=(29, 59))
    assert dr1.review_exit(position, above, mean_history) is None
    assert dr1.review_exit(position, below_spot, mean_history) == ExitReason.SPOT_THROUGH_MEAN
    assert dr1.review_exit(position, below_spot, ()) is None  # no window of history: the mean cannot be judged


def test_a_price_that_cannot_be_judged_never_fires_a_price_rule():
    driver, position = opened_ps4()
    _, snapshot = b.scene()
    leg = position.legs[0].key
    broken = replace(snapshot, quotes={**snapshot.quotes, leg: SlotQuote(None, 5.0, None, 100, None, False)})
    wrecked = repriced(broken, 0.01)  # a profit target would be reached on every other leg
    assert net_if_closed(position, wrecked) is None
    assert driver.review_exit(position, wrecked, ()) is None
    missing = replace(snapshot, quotes={k: q for k, q in snapshot.quotes.items() if k != leg})
    assert driver.review_exit(position, missing, ()) is None


def test_an_exit_rule_with_no_numbers_waits_for_expiry():
    rule = ExitPlan()
    driver, position = opened_ps4()
    assert rule.review(position, on_day(25), (), b.CALENDAR) is None
    assert rule.review(position, on_day(30), (), b.CALENDAR) == ExitReason.EXPIRY


@pytest.mark.parametrize("days_after", [31, 45])
def test_a_position_past_its_expiry_still_ends_in_expiry(days_after):
    driver, position = opened_ps4()
    _, snapshot = b.scene(session=b.SESSION + timedelta(days=days_after), days=(35,))
    assert driver.review_exit(position, snapshot, ()) == ExitReason.EXPIRY

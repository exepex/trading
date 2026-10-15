"""Story E2b criterion 3: the half-spread paid reads each fill's touch from the execution snapshot the row names
(hash-checked); a fill whose touch cannot be read is "touch unknown" (counted, never zero); a settlement is left out."""

from datetime import date

from fno.constants import FILL_CLOSE, FILL_OPEN, FILL_SETTLE, SIDE_BUY, SIDE_SELL
from fno.scorecard.touches import half_spread

from .history import LONG, SHORT, SNAPSHOT_SHA, TouchSnapshots

DAY = date(2026, 10, 14)


def row(leg, side, price, snapshot="s1", sha=SNAPSHOT_SHA, action=FILL_OPEN, contract_id=""):
    return {"action": action, "filled_at": "2026-10-14T15:15:40+05:30", "snapshot_id": snapshot, "snapshot_sha256": sha,
            "expiry": leg.expiry.isoformat(), "strike": repr(float(leg.leg.strike)), "type": leg.leg.kind,
            "quote_contract_id": contract_id, "side": side, "price": repr(price), "units": "65"}  # fmt: skip


def snapshots():
    source = TouchSnapshots()
    source.add(DAY, "s1", LONG, 20.0, 21.0)  # mid 20.5
    source.add(DAY, "s1", SHORT, 50.0, 52.0)  # mid 51.0
    return source


def test_the_half_spread_is_the_touch_s_half_width_by_hand():
    spread = half_spread([row(LONG, SIDE_BUY, 21.0), row(SHORT, SIDE_SELL, 50.0)], snapshots())
    assert (spread.units, spread.per_unit, spread.touch_unknown) == (130, (0.5 * 65 + 1.0 * 65) / 130, 0)


def test_an_unreadable_snapshot_a_hash_mismatch_or_a_missing_quote_is_touch_unknown_never_zero():
    fills = [row(LONG, SIDE_BUY, 21.0, snapshot="gone"), row(LONG, SIDE_BUY, 21.0, sha="f" * 64),
             row(SHORT, SIDE_SELL, 50.0, contract_id="OTHER"), row(LONG, SIDE_BUY, 21.0)]  # fmt: skip
    source = snapshots()
    source.add(DAY, "s1", SHORT, 50.0, 52.0)
    source.quotes[(DAY, "s1")][(SHORT.expiry, float(SHORT.leg.strike), SHORT.leg.kind)] = source.quotes[(DAY, "s1")][
        (SHORT.expiry, float(SHORT.leg.strike), SHORT.leg.kind)
    ].__class__("REAL", SHORT.expiry, float(SHORT.leg.strike), SHORT.leg.kind, 50.0, 52.0, 1e6, 1e6, True, "", True)
    spread = half_spread(fills, source)
    assert (spread.units, spread.per_unit, spread.touch_unknown) == (65, 0.5, 3)


def test_nothing_known_gives_no_average_and_settlements_are_left_out():
    settle = row(LONG, SIDE_SELL, 3.0, snapshot="settlement", action=FILL_SETTLE)
    assert half_spread([settle], snapshots()) == half_spread([], snapshots())
    assert half_spread([], snapshots()).per_unit is None
    unknown = half_spread([row(LONG, SIDE_BUY, 21.0, snapshot="gone", action=FILL_CLOSE)], snapshots())
    assert (unknown.units, unknown.per_unit, unknown.touch_unknown) == (0, None, 1)


def test_the_report_prints_the_touch_unknown_count(root, make_run):
    from fno.constants import BOOK1_RULES
    from fno.scorecard.report import card_lines

    from .history import trade
    from .test_scorecard import card

    trade(root, BOOK1_RULES, "fly-a-v1", "t1", DAY)
    lines = card_lines(card(make_run))
    assert any("touch unknown on 0 fill(s)" in line for line in lines), lines

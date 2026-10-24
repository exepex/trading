"""Story G10 completion, criterion 3: the pack builder's boundary and empty cases beside part 2's tests: 14:29:59 and
14:40:01 out, 14:40:00 in; `last_trade_time` never the observation time; the day before a monthly expiry (Monday 26
Oct: October has 1 day left, so IV30 is November's alone, flagged); a capture with no valid row."""

from datetime import date

from tests.v4_pack.capture_fixture import NOV, at, meta, row, rows
from tests.v4_pack.test_pack_builder import build

OCT = date(2026, 10, 27)
MONDAY = date(2026, 10, 26)


def test_the_window_s_two_edges_and_the_quote_time():
    edges = [
        row(NOV, 25100.0, "CE", 420.0, received=at(14, 29, 59)),
        row(NOV, 25100.0, "PE", 320.0, received=at(14, 40)),
    ]
    chain = build(capture_rows=rows() + edges).pack.chain
    found = {(q.expiry, q.strike, q.kind): q for q in chain}
    assert (NOV, 25100.0, "CE") not in found and found[(NOV, 25100.0, "PE")].observed_at.isoformat() == at(14, 40)
    quote = found[(NOV, 25000.0, "CE")]
    assert quote.observed_at.isoformat() == at(14, 31, 5) and quote.last_trade_time.isoformat() == at(14, 29, 50)


def test_the_day_before_a_monthly_expiry_takes_e_as_tomorrow_and_flags_iv30_from_the_next_monthly():
    chains = [{"expiry": e.isoformat(), "spot": spot, "response_received_at": at(14, 30, 2, MONDAY)}
              for e, spot in ((OCT, 25000.0), (NOV, 25001.0))]  # fmt: skip
    day_meta = meta(chains=chains, levels_received_at=at(14, 30, 6, MONDAY))
    legs = ((OCT, "CE", 60.0), (OCT, "PE", 60.0), (NOV, "CE", 470.0), (NOV, "PE", 270.0))
    day_rows = [row(e, 25000.0, k, m, received=at(14, 31, 5, MONDAY)) for e, k, m in legs]
    pack = build(day_meta, day_rows, day=MONDAY).pack
    assert pack.future.expiry == OCT  # e: the nearest monthly strictly after the day, one day left
    assert pack.iv30.flagged and pack.iv30.expiries == (NOV,)  # October's 1 day cannot bracket 30 days


def test_a_capture_with_no_valid_row_gives_system_late():
    built = build(capture_rows=[{**r, "valid": "false"} for r in rows()])
    assert built.pack is None and built.reasons == ("no valid ATM call and put of e in the window",)

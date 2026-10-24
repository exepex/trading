"""FL1-1c: why a recent forecast missed. A reason appears only when a fact crosses its stated threshold (and a flow
only when it pushes the way of the miss); otherwise "no clear reason in our data", never a guess."""

from datetime import date

from fno.forecast_lab.page.reasons import NO_REASON, Facts, reasons, recent_misses

from .page_builders import days, outcome

TUE, MON = date(2026, 10, 13), date(2026, 10, 12)


def test_no_fact_over_its_threshold_gives_no_clear_reason():
    facts = Facts(vix={MON: 14.0, TUE: 15.0}, flows={TUE: (-3999.0, 3999.0)})  # +7% VIX, flows under 4,000
    assert reasons(TUE, MON, facts, above=True) == (NO_REASON,)


def test_each_fact_over_its_threshold_is_a_reason():
    facts = Facts(vix={MON: 14.0, TUE: 15.5}, events={TUE: "RBI policy decision"}, expiries=frozenset({TUE}),
                  brent={date(2026, 10, 9): 100.0, MON: 104.0}, usdinr={date(2026, 10, 9): 88.0, MON: 88.5},
                  flows={TUE: (-5285.0, 4100.0)})  # fmt: skip
    assert reasons(TUE, MON, facts, above=False) == (
        "India VIX jumped from 14.0 to 15.5", "scheduled event: RBI policy decision", "NIFTY F&O expiry day",
        "Brent oil moved +4.0% just before", "the rupee (USD/INR) moved +0.6% just before",
        "FIIs sold a net Rs 5,285 crore that day",
    )  # fmt: skip


def test_a_flow_pushing_against_the_miss_is_no_reason_for_it():
    facts = Facts(flows={TUE: (-5285.0, 4100.0)})
    assert reasons(TUE, MON, facts, above=True) == ("DIIs bought a net Rs 4,100 crore that day",)


def test_the_last_30_sessions_misses_newest_first_with_how_far_outside():
    sessions = days(32)
    points = [outcome(d, 1000.0) for d in sessions]
    points[-1], points[-3], points[2], points[1] = (
        outcome(sessions[-1], 1031.0),
        outcome(sessions[-3], 960.0),
        outcome(sessions[2], 970.0),  # the 30th session back: still in the window
        outcome(sessions[1], 900.0),  # the 31st: older than the window
    )
    misses = recent_misses(points, lambda d: sessions[sessions.index(d) - 1], Facts())
    assert [(m.day, m.side, round(m.points), m.reasons) for m in misses] == [
        (sessions[-1], "above", 11, (NO_REASON,)), (sessions[-3], "below", 20, (NO_REASON,)),
        (sessions[2], "below", 10, (NO_REASON,))]  # fmt: skip

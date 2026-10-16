"""FT1 criteria 6, 7 and 9 on a synthetic window: every registered cell, the paired difference, the flip shares, the
exclusion counts, the spread caveat and the "not measured" lines reach the report; only the two flip shares leave the
option P&L; the same run twice gives the same results (PROTOCOL.md sections 8-15 and 20)."""

import json
import math
from datetime import date, time

import pytest
from ft1study.bars import Bar
from ft1study.observe import Market, Observer
from ft1study.report import NOT_MEASURED, render
from ft1study.steps import prepare, results
from ft1study.times import Moment

from tests.research_ft1.ft1_fakes import TERMS, FakeCalendar, contracts, index_book, structures

EXPIRIES = [date(2025, 1, 30), date(2025, 2, 27), date(2025, 3, 27), date(2025, 4, 24)]
FIRST, LAST = date(2025, 1, 1), date(2025, 2, 28)
CAL = FakeCalendar(holidays={date(2025, 2, 26)})
MARKS = [time(9, 45), time(10, 15), time(14, 0), time(14, 15), time(14, 45), time(15, 0), time(15, 15)]
MONTHS = {"Jan": 1, "Feb": 2, "Mar": 3, "Apr": 4}


def level(day: date, at: time) -> float:
    return 23000 + 40 * math.sin(day.toordinal() / 3) + at.hour * 2 + at.minute / 10


INDEX = index_book({(d, t): level(d, t) for d in CAL.sessions(FIRST, date(2025, 3, 7)) for t in MARKS})


def bar(symbol: str, moment: Moment) -> Bar | None:
    parts = symbol.split("-")
    spot = level(moment.day, moment.at)
    if parts[-1] == "FUT":
        return Bar(spot + 25, 500.0)
    strike, kind = float(parts[3]), parts[4]
    days = (date(2000 + int(parts[2][-2:]), MONTHS[parts[2][2:5]], int(parts[2][:2])) - moment.day).days
    intrinsic = max(spot - strike, 0) if kind == "CE" else max(strike - spot, 0)
    return Bar(round(intrinsic + 6 * math.sqrt(max(days, 1)) * math.exp(-abs(spot - strike) / 400) + 1, 2), 50.0)


SNAPSHOT = "\n".join(["strike,spot,valid,bid,ask", "23000,23000,true,100,101", "23100,23000,true,90,91.5",
                      "23500,23000,true,20,21", "23600,23000,false,,", "22500,23000,true,25,26.2"])  # fmt: skip


def run() -> dict:
    listed = contracts(EXPIRIES, FIRST, date(2025, 4, 24), CAL, settlement={e: 23050.0 for e in EXPIRIES[:3]})
    prepared = prepare(CAL, listed, structures(), INDEX, FIRST, LAST)
    observer = Observer(Market(bar, INDEX, {}, listed.settlement, CAL.next_session), TERMS)
    return results(prepared, observer, [s.code for s in structures()], 65, [SNAPSHOT], f"{FIRST} to {LAST}", "abc")


@pytest.fixture(scope="module")
def found() -> dict:
    return run()


def test_every_registered_cell_is_computed_with_the_e4_rows_labelled(found):
    cells = {c["cell"]: c for c in found["analysis"]["cells"]}
    assert len(cells) == 9 * 6 + 7 * 2  # six main cells a family, two width-sensitivity cells per width family
    assert all(c["status"] == "ok" for c in cells.values())
    assert {name for name, c in cells.items() if c["e4_snapshot"]} == {
        f"{f} w{w} {t} R{r}" for f, w in [(s.code, 0 if s.code in ("LC", "LP") else 200) for s in structures()]
        for t, r in (("15:00", 5), ("14:00", 60))}  # fmt: skip


def test_a_holiday_leaves_no_day_out_and_its_eve_fills_after_2_nights(found):
    left = found["days_left_out"]
    assert left == {"decision days kept": len(CAL.sessions(FIRST, LAST))}
    sf = next(c for c in found["analysis"]["cells"] if c["cell"] == "SF w200 15:00 R60")
    assert sf["splits"]["nights"]["2"] == {"n": 1, "status": "too few days"}  # 25 Feb to 27 Feb


def test_only_the_two_flip_shares_leave_the_option_pnl(found):
    for flips in found["analysis"]["flips"]:
        assert set(flips) == {"cell", "status", "expiries", "not_settled", "bad_flip_share", "good_flip_share"}
    text = json.dumps(found).lower() + render(found).lower()
    assert "pnl" not in text and "win rate" not in text and 'wins"' not in text


def test_the_report_carries_every_section_and_the_not_measured_lines(found):
    text = render(found)
    for line in NOT_MEASURED:
        assert line in text
    for heading in ("Exploratory measurement", "Days left out", "The owner's choice", "Flip share", "Width sensitivity",
                    "### nights", "### gap band", "### VIX band", "### sessions to expiry", "Spread caveat",
                    "(= E4 15:15)", "Window: 2025-01-01 to 2025-02-28"):  # fmt: skip
        assert heading in text
    assert found["spreads"]["families"]["SF"]["entry_spread_points"] == pytest.approx(
        4 * 0.62
    )  # median of 0.5 and 0.75, A4 rounds


def test_the_same_run_twice_gives_the_same_results(found):
    assert run() == found

"""FT1 criteria 2, 7 and 9 in the report: a cell that cannot be read prints its status and no number, the flip table
prints shares only, and the two hand-check days carry what a judge recomputes from the raw answers."""

from datetime import time

import pytest
from ft1study import handcheck
from ft1study.handcheck import flip_label
from ft1study.observe import Market, Observer
from ft1study.report import render
from ft1study.steps import prepare

from tests.research_ft1.ft1_fakes import TERMS, contracts, structures
from tests.research_ft1.test_ft1_end_to_end import CAL, EXPIRIES, FIRST, INDEX, LAST, bar, run


@pytest.fixture(scope="module")
def found() -> dict:
    return run()


def test_a_cell_that_cannot_be_read_prints_its_status_and_no_number(found):
    cells = [dict(c) for c in found["analysis"]["cells"]]
    sf = next(c for c in cells if c["cell"] == "SF w200 15:00 R60")
    blocked = {k: sf[k] for k in ("cell", "family", "width", "eligible_days", "n", "left_out", "e4_snapshot")}
    cells[cells.index(sf)] = blocked | {"status": "insufficient data", "n": 3}
    flips = [f if f["cell"] != "SF w200 15:00 R60 flips" else {"cell": f["cell"], "status": "insufficient data"}
             for f in found["analysis"]["flips"]]  # fmt: skip
    text = render(found | {"analysis": found["analysis"] | {"cells": cells, "flips": flips}})
    row = next(line for line in text.splitlines() if line.startswith("| SF w200 15:00 R60 |"))
    assert "insufficient data" in row and row.count("[") == 0
    flip_row = next(line for line in text.splitlines() if line.startswith("| SF w200 15:00 R60 flips |"))
    assert "insufficient data" in flip_row and "%" not in flip_row


@pytest.mark.parametrize(("decision", "fill", "label"), [(5.0, -1.0, "bad flip"), (5.0, 0.0, "bad flip"),
                         (0.0, 2.0, "good flip"), (-3.0, -1.0, "no flip"), (4.0, 9.0, "no flip"),
                         (None, None, "not settled")])  # fmt: skip
def test_the_flip_label(decision, fill, label):
    assert flip_label(decision, fill) == label


def test_the_hand_check_days_carry_strikes_prices_c_and_the_flip(monkeypatch):
    monkeypatch.setattr(handcheck, "HAND_DAYS", {time(15, 0): 3, time(14, 0): 5})
    listed = contracts(EXPIRIES, FIRST, EXPIRIES[-1], CAL, settlement={e: 23050.0 for e in EXPIRIES[:3]})
    prepared = prepare(CAL, listed, structures(), INDEX, FIRST, LAST)
    observer = Observer(Market(bar, INDEX, {}, listed.settlement, CAL.next_session), TERMS)
    rows = handcheck.hand_check(prepared.days, prepared.entries, observer)
    assert [(r["day"], r["decision"], r["family"]) for r in rows] == [
        (prepared.days[3].day, "15:00", "SF"), (prepared.days[3].day, "15:00", "LC"),
        (prepared.days[5].day, "14:00", "SF"), (prepared.days[5].day, "14:00", "LC")]  # fmt: skip
    sf = rows[0]
    assert len(sf["legs"]) == 4 and sorted(sf["fills"]) == [5, 30, 60]
    fill = sf["fills"][60]
    signed = [side for _, side in sf["legs"]]
    by_hand = sum(s * p for s, p in zip(signed, fill["prices"])) - sum(
        s * p for s, p in zip(signed, sf["decision_prices"])
    )
    assert fill["c"] == pytest.approx(by_hand) and fill["flip"] in ("bad flip", "good flip", "no flip")

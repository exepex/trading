"""Judge 83 addendum 2: C4 prices only from quotes A4's rule finds usable (`ExecutionQuote.a4_problem`), the rule
Book 1 prices by. A bad at-the-money quote must not move the parity forward or any stress figure, and a leg priced on
a bad quote fails."""

import pytest

from fno.checks.validity_chain import PricedChain
from fno.checks.validity_evidence import EvidenceReader
from fno.checks.validity_limits import PRICED
from fno.quotes.recorder import DATASET
from tests.checks.builders import committed_record
from tests.checks.validity_builders import DAY, check, committed_store, failed, mid, snapshot_rows

BAD = {
    "crossed": {"bid": "260", "ask": "250"},
    "not valid (no trade today)": {"valid": "false", "invalid_reason": "no trade today"},
    "no size": {"ask_qty": "0"},
    "one-sided": {"bid": ""},
}


def rows_with(strike: float, kind: str, change: dict, expiry: str = "2026-10-27") -> list[dict]:
    rows = snapshot_rows()
    for r in rows:
        if (float(r["strike"]), r["type"], r["expiry"]) == (strike, kind, expiry):
            r.update(change)
    return rows


def chain(rows) -> PricedChain:
    store = committed_store(rows)
    evidence, problems = EvidenceReader(store, DATASET).read(DAY, committed_record(store, DAY, "exec"))
    assert problems == []
    return PricedChain(evidence, DAY, 0.065)


def stress_numbers(report) -> dict:
    return {r.name: r.numbers for r in report.results if r.name in PRICED}


@pytest.mark.parametrize("bad", sorted(BAD))
def test_a_bad_quote_has_no_mid(bad):
    contract = next(r["contract_id"] for r in snapshot_rows() if (r["strike"], r["type"]) == ("25100", "PE"))
    assert contract not in chain(rows_with(25_100.0, "PE", BAD[bad])).quotes
    assert contract in chain(snapshot_rows()).quotes


def test_a_bad_at_the_money_quote_does_not_move_the_forward_or_the_stress():
    """The 25,100 call is marked invalid with a mid equal to the put's: if counted, parity picks 25,100 (C - P = 0) and
    the forward moves from 25,000 to 25,100. It is not counted: the forward and every stress figure are unchanged."""
    put_mid = mid(25_100, "PE")
    bad = {"bid": f"{put_mid - 0.5:g}", "ask": f"{put_mid + 0.5:g}"} | BAD["not valid (no trade today)"]
    rows = rows_with(25_100.0, "CE", bad)
    assert chain(rows).forward("2026-10-27") == pytest.approx(chain(snapshot_rows()).forward("2026-10-27"))
    assert chain(snapshot_rows()).forward("2026-10-27") == pytest.approx(25_000.0)
    clean, dirty = check(), check(store=committed_store(rows))
    assert clean.ok and dirty.ok and stress_numbers(dirty) == stress_numbers(clean)


@pytest.mark.parametrize("bad", sorted(BAD))
def test_a_leg_on_a_bad_quote_fails(bad):
    report = check(store=committed_store(rows_with(25_200.0, "CE", BAD[bad])))
    assert failed(report) == {"leg 2026-10-27 25200 CE", *PRICED}
    leg = next(r for r in report.failures if r.name.startswith("leg"))
    assert "not usable by A4's rule" in leg.reason

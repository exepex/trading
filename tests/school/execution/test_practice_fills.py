"""Design A (orchestrator, 22 Oct 2026): a quote whose displayed size was never measured (`sizes_measured=False`, the
simulator's history) fills under practice rules with no size limit, at the same touch and charges; the live port
refuses the same entry as `size_not_measured` and never fills from it. A quote missing a price stays one-sided under
any rules, and no size sentinel stands in for "unmeasured" anywhere in `fno/`."""

from dataclasses import replace
from pathlib import Path

import pytest

from fno.school.constants import ExitState, RefusalReason
from fno.school.execution.practice_wiring import PRACTICE
from fno.school.execution.school_fills import SchoolFills
from tests.school.contracts import builders as b

from .school_builders import AT, CHARGES, fills, settlement_source

FNO = Path(__file__).parents[3] / "fno"


def unmeasured(bid: float | None = 10.0, ask: float | None = 11.0):
    return replace(b.quote(bid or 1.0, ask or 2.0), bid=bid, ask=ask, bid_qty=None, ask_qty=None, sizes_measured=False)


UNMEASURED = b.snapshot(quotes={b.key(1000.0): unmeasured(), b.key(900.0): unmeasured(4.0, 5.0)})


@pytest.fixture
def practice(tmp_path):
    return SchoolFills(CHARGES, settlement_source(tmp_path), PRACTICE)


def test_a_practice_entry_on_an_unmeasured_quote_fills_at_the_touch(practice, tmp_path):
    result = practice.enter(b.sealed(), UNMEASURED, b.seal(), AT)
    measured = fills(tmp_path).enter(b.sealed(), b.snapshot(), b.seal(), AT)
    assert not result.refused and result.legs == measured.legs  # same touch, units and charges as a measured quote


def test_the_live_port_refuses_the_same_entry_as_size_not_measured(tmp_path):
    result = fills(tmp_path).enter(b.sealed(), UNMEASURED, b.seal(), AT)
    assert result.refused == (RefusalReason.SIZE_NOT_MEASURED,) and not result.legs


def test_a_practice_exit_closes_and_a_live_exit_waits(practice, tmp_path):
    closed = practice.exit(b.position(), UNMEASURED, "cd" * 32, b.seal(), AT)
    assert len(closed.legs) == 2 and not closed.refused
    waiting = fills(tmp_path).exit(b.position(), UNMEASURED, "cd" * 32, b.seal(), AT)
    assert waiting.state == ExitState.EXIT_WAITING_QUOTE and not waiting.legs


@pytest.mark.parametrize("side", ["bid", "ask"])
def test_a_missing_price_stays_one_sided_under_either_rules(practice, tmp_path, side):
    """Under live rules too: only a quote priced on both sides is `size_not_measured`."""
    broken = unmeasured(**{side: None})
    snapshot = b.snapshot(quotes={b.key(1000.0): broken, b.key(900.0): b.quote(4.0, 5.0)})
    for port in (practice, fills(tmp_path)):
        assert port.enter(b.sealed(), snapshot, b.seal(), AT).refused == (RefusalReason.ONE_SIDED_QUOTE,)


def test_no_size_sentinel_stands_in_for_unmeasured():
    for path in FNO.rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        assert "10**9" not in text and "SIZE_GATE_WAIVED" not in text, path

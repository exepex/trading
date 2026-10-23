"""Practice quote rules (orchestrator, 22 Oct 2026, design A; story 7.2): the simulator's roots alone build with
`QuoteRules(practice=True)`. Under them a size nobody measured passes the size and sell-back checks with the note
"size gate not tested in practice"; every other law, the quote's validity and two sides included, is the live law.
Live builds `LIVE`, refuses the same quote as `size_not_measured`, and cannot reach the practice path: no module
outside the simulator imports a `practice_wiring`, and only the two safety wiring modules call `laws_with`."""

import ast
from dataclasses import replace
from pathlib import Path

import pytest

from fno.school.constants import RefusalReason, RoadCode
from fno.school.execution.quote_rules import LIVE, PRACTICE_SIZE_NOTE, QuoteRules
from fno.school.safety.law_set import refusals
from fno.school.safety.practice_wiring import build_practice_safety_laws
from fno.school.safety.quote_laws import SIZE_REASONS, QuoteGateLaw
from fno.school.safety.wiring import build_safety_laws
from tests.school.contracts import builders as b
from tests.school.contracts.test_boundaries import SCHOOL, imports
from tests.school.execution.test_practice_fills import UNMEASURED, unmeasured

from .law_builders import CFG, SETTINGS, FixedMargin, view

SLOT = {RoadCode.BANKNIFTY_MONTHLY: b.snapshot()}
LIVE_LAWS = build_safety_laws(CFG, SETTINGS, SLOT, FixedMargin())
PRACTICE_LAWS = build_practice_safety_laws(CFG, SETTINGS, SLOT, FixedMargin())
SHORT = b.snapshot(quotes={b.key(1000.0): b.quote(size=1), b.key(900.0): replace(b.quote(4.0, 5.0), bid_qty=1)})
FNO = SCHOOL.parent
PRACTICE_ROOT = "school/execution/practice_wiring.py"
PRACTICE_ONLY = ("school/simulator/", "school/safety/practice_wiring.py", PRACTICE_ROOT)
FNO_FILES = sorted(p for p in FNO.rglob("*.py") if "__pycache__" not in p.parts)


def by_name(results):
    return {r.law: r for r in results}


def test_an_unmeasured_size_passes_in_practice_with_the_note_and_is_refused_live():
    practice = by_name(PRACTICE_LAWS.check(b.put_spread(), view(), UNMEASURED, b.SESSION))
    live = refusals(LIVE_LAWS.check(b.put_spread(), view(), UNMEASURED, b.SESSION))
    assert refusals(practice.values()) == ()
    assert all(practice[f"quote_gate:{reason}"].note == PRACTICE_SIZE_NOTE for reason in SIZE_REASONS)
    assert live == (RefusalReason.SIZE_NOT_MEASURED,)


@pytest.mark.parametrize(
    ("snapshot", "refused"),
    [(SHORT, (RefusalReason.SIZE_ABOVE_DISPLAYED, RefusalReason.PROTECTION_UNSELLABLE)), (b.snapshot(), ())],
    ids=["too_small", "enough"],
)
def test_a_measured_size_is_judged_in_practice_as_live_and_carries_no_note(snapshot, refused):
    """Practice waives only what nobody measured: a shown size is judged, and its result never says untested."""
    for laws in (PRACTICE_LAWS, LIVE_LAWS):
        found = by_name(laws.check(b.put_spread(), view(), snapshot, b.SESSION))
        assert refusals(found.values()) == refused
        assert all(r.note == "" for r in found.values() if r.law.startswith("quote_gate:"))


@pytest.mark.parametrize(
    ("quote", "reason"),
    [(None, RefusalReason.MISSING_QUOTE), (unmeasured(ask=None), RefusalReason.ONE_SIDED_QUOTE),
     (replace(unmeasured(), valid=False), RefusalReason.ONE_SIDED_QUOTE)],
    ids=["missing", "no_ask", "not_valid"],
)  # fmt: skip
def test_practice_never_passes_a_missing_one_sided_or_invalid_quote(quote, reason):
    quotes = dict(UNMEASURED.quotes) | ({} if quote is None else {b.key(1000.0): quote})
    if quote is None:
        del quotes[b.key(1000.0)]
    found = refusals(PRACTICE_LAWS.check(b.put_spread(), view(), b.snapshot(quotes=quotes), b.SESSION))
    assert found[0] == reason


def test_the_live_root_builds_live_rules_only():
    quote_laws = [law for law in LIVE_LAWS.laws if isinstance(law, QuoteGateLaw)]
    assert len(quote_laws) == 5 and all(law.rules == LIVE and not law.rules.practice for law in quote_laws)


def test_quote_rules_take_practice_by_name_only():
    """Judge 488.6 note 1: a positional `QuoteRules(True)` would slip past the text scan below, so it cannot exist."""
    with pytest.raises(TypeError):
        QuoteRules(True)  # type: ignore[misc]


def quote_rules_calls(path: Path) -> int:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    return sum(isinstance(n, ast.Call) and getattr(n.func, "id", getattr(n.func, "attr", "")) == "QuoteRules"
               for n in ast.walk(tree))  # fmt: skip


@pytest.mark.parametrize("path", FNO_FILES, ids=lambda p: p.relative_to(FNO).as_posix())
def test_no_live_module_reaches_the_practice_path(path):
    """Across all of `fno/`, not only the school (judge 488.6 note 1)."""
    relative = path.relative_to(FNO).as_posix()
    names = imports(path)
    if not relative.startswith(PRACTICE_ONLY):
        assert not [n for n in names if "practice_wiring" in n], f"{relative} imports a practice composition"
    if relative not in ("school/safety/wiring.py", "school/safety/practice_wiring.py"):
        assert not [n for n in names if n.endswith(".laws_with")], f"{relative} builds laws with chosen rules"
    if relative != PRACTICE_ROOT:
        assert "practice=True" not in path.read_text(encoding="utf-8"), f"{relative} builds practice rules"
    if relative not in (PRACTICE_ROOT, "school/execution/quote_rules.py"):
        assert not quote_rules_calls(path), f"{relative} builds its own quote rules"

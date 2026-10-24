"""MS-P1m and MS-P1d (agreed, 22 Oct 2026): the desk's two decision codecs rebuild terms as `TradeTerms(**asdict(...))`,
which a school `RoadTradeTerms` (index, expiry, legs, lot) cannot survive. The school never hands its terms to them:
no school module imports either codec, and the school's composition roots load neither."""

import subprocess
import sys
from dataclasses import asdict
from datetime import date

import pytest

from fno.nse_margins.road_trades import RoadTradeTerms
from fno.research_engine.structures import BOUGHT, SOLD, Leg
from fno.risk.inputs import TradeTerms
from tests.school.contracts.test_boundaries import FILES, ROOT, SCHOOL, imports

DESK_CODECS = ("fno.desk.owner_timing.order_record", "fno.playbook.decision_codec")
ROOTS = ("fno.school.safety.wiring", "fno.school.accounts.wiring", "fno.school.execution.wiring")


def test_the_round_trip_those_codecs_use_cannot_carry_school_terms():
    terms = RoadTradeTerms("PCS", 100.0, 1, "NIFTY", date(2026, 11, 24), (Leg(1000.0, "PE", SOLD),
                                                                         Leg(900.0, "PE", BOUGHT)), 65)  # fmt: skip
    with pytest.raises(TypeError):
        TradeTerms(**asdict(terms))


@pytest.mark.parametrize("path", FILES, ids=lambda p: p.relative_to(SCHOOL).as_posix())
def test_no_school_module_imports_a_desk_codec(path):
    bad = [n for n in imports(path) if any(n == c or n.startswith(c + ".") for c in DESK_CODECS)]
    assert not bad, f"{path.name} imports {bad}"


def test_the_school_s_composition_roots_load_neither_codec():
    code = f"import importlib, sys\nfor m in {ROOTS!r}: importlib.import_module(m)\nprint(sorted(sys.modules))"
    loaded = subprocess.run([sys.executable, "-c", code], cwd=ROOT, capture_output=True, text=True, check=True).stdout
    assert not [c for c in DESK_CODECS if f"'{c}'" in loaded]

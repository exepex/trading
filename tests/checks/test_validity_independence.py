"""Story C4 (orchestrator's condition, judge 83): the hard-validity code is independent of the code that proposes and
risk-checks trades. It fails if any `fno/checks/validity*.py` names one of these modules, or if importing them loads
one at any depth:
- the proposer's cost, structure and pricing modules;
- C2's rules, brake, stress, margins and settings;
- E1's account arithmetic;
- D2's allocation."""

import subprocess
import sys
from pathlib import Path

import pytest

from tools.check_imports import ROOT, imported_modules

PROPOSER = (
    "fno.costs", "fno.research_engine.cycle_costs", "fno.research_engine.structures", "fno.research_engine.simulator",
    "fno.research_engine.leg_prices", "fno.risk.trade_costs", "fno.risk.rules", "fno.risk.manager", "fno.risk.margins",
    "fno.risk.stress", "fno.risk.drawdown", "fno.risk.overrides", "fno.risk.book_view", "fno.risk.settings",
    "fno.research_engine.implied_vol", "fno.books.account", "fno.books.equity", "fno.books.fills",
    "fno.playbook.candidates", "fno.playbook.allocation", "fno.playbook.book_effects",
)  # fmt: skip
VALIDITY_FILES = sorted((ROOT / "fno" / "checks").glob("validity*.py"))


def _proposer(name: str) -> bool:
    return any(name == module or name.startswith(module + ".") for module in PROPOSER)


def test_the_validity_files_exist():
    names = {p.name for p in VALIDITY_FILES}
    assert {
        "validity.py",
        "validity_money.py",
        "validity_evidence.py",
        "validity_adapter.py",
        "validity_pricing.py",
        "validity_stress.py",
        "validity_margin.py",
        "validity_drawdown.py",
        "validity_account.py",
    } <= names


@pytest.mark.parametrize("path", VALIDITY_FILES, ids=lambda p: p.name)
def test_no_validity_file_imports_the_proposers_code(path: Path):
    assert [name for name in imported_modules(path) if _proposer(name)] == []


def test_importing_the_validity_code_loads_none_of_the_proposers_modules():
    modules = ", ".join(f"fno.checks.{p.stem}" for p in VALIDITY_FILES)
    code = f"import sys, {modules}; print('\\n'.join(sorted(sys.modules)))"
    loaded = subprocess.run([sys.executable, "-B", "-c", code], cwd=ROOT, capture_output=True, text=True, check=True)
    assert [name for name in loaded.stdout.split() if _proposer(name)] == []

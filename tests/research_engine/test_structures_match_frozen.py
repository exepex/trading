"""Story STR1 criterion 9 (judge C, option b): the frozen B2 code at experiment 1's run commit and today's code give
the same legs, payoff bounds and modelled maximum loss for SF, SC and BF on every cycle of both experiment 1 periods
(2019-26), at every research width, on the entry day's real panel chain and closes. The frozen `structures.py` and
`cycle_costs.py` are loaded from git (`0c1c957`), not copied. Option (a), the full overlay run of both periods on a
worktree of `0c1c957`, is in response 106 (it reproduces both published hashes). Needs full git history."""

from __future__ import annotations

import importlib.util
import subprocess
import sys

import pytest

from fno.composition import build_cycles, build_structures
from fno.config import ROOT, load_app_config
from fno.constants import NIFTY_SYMBOL
from fno.research_data.panel_reader import read_nifty_panel
from fno.research_engine.cycle_costs import WIDTHS, CycleTerms, PositionCosts
from fno.research_engine.cycles import cycle_rows
from fno.research_engine.leg_prices import contracts_on, leg_price
from fno.research_engine.structures import payoff_bounds
from fno.storage.wiring import PANEL_FOLDER

RUN_COMMIT = "0c1c957eb49cfa3c2ea3efb6b93befa66d6b6928"  # tests/research/test_experiment_1_frozen.py
YEARS = range(2019, 2027)  # discovery 2024-26 and challenge 2019-23


def _frozen(name: str, source_name: str, replace: tuple[str, str] | None = None):
    text = subprocess.run(["git", "show", f"{RUN_COMMIT}:fno/research_engine/{source_name}.py"], cwd=ROOT,
                          capture_output=True, text=True, check=True).stdout  # fmt: skip
    if replace:
        text = text.replace(*replace)
    spec = importlib.util.spec_from_loader(f"fno.research_engine.{name}", loader=None)
    module = importlib.util.module_from_spec(spec)
    module.__package__ = "fno.research_engine"
    sys.modules[spec.name] = module
    exec(compile(text, f"{RUN_COMMIT[:7]}:{source_name}.py", "exec"), module.__dict__)
    return module


@pytest.fixture(scope="module")
def frozen():
    structures = _frozen("_frozen_structures", "structures")
    costs = _frozen(
        "_frozen_cycle_costs", "cycle_costs", ("from .structures import", "from ._frozen_structures import")
    )
    return structures, costs


@pytest.fixture(scope="module")
def cases():
    """(cycle, spot, quotes) on each cycle's entry day, every cycle of 2019-26 with entry-day data."""
    panel = read_nifty_panel(PANEL_FOLDER, YEARS, cycle_rows)
    found = []
    for cycle in build_cycles(panel):
        session = panel.session_on(cycle.entry_day)
        quotes = contracts_on(panel.options_on(cycle.entry_day, cycle.expiry)) if cycle.has_entry_window else {}
        if session is not None and session.underlying is not None and quotes:
            found.append((cycle, session.underlying, quotes))
    return found


def _shown(legs):
    return None if legs is None else [(leg.strike, leg.kind, leg.side) for leg in legs]


def test_both_periods_are_covered(cases):
    years = {cycle.entry_day.year for cycle, _, _ in cases}
    assert {2019, 2023, 2024, 2026} <= years and len(cases) >= 90  # 60 challenge + 33 discovery cycles


def test_frozen_and_current_b2_agree_on_every_cycle_structure_and_width(frozen, cases):
    old_structures, old_costs = frozen
    terms = CycleTerms(lot=load_app_config()["lot_sizes"][NIFTY_SYMBOL], charges=load_app_config()["charges"])
    old_cost, new_cost = old_costs.PositionCosts(old_costs.CycleTerms(**vars(terms))), PositionCosts(terms)
    old_by_code = {s.code: s for s in (old_structures.ShortIronFly(), old_structures.ShortCondor(),
                                       old_structures.LongIronFly())}  # fmt: skip
    different, compared = [], 0
    for cycle, spot, quotes in cases:
        chain = frozenset(quotes)
        for new in build_structures():
            for width in WIDTHS:
                old_legs, new_legs = old_by_code[new.code].legs(chain, spot, width), new.legs(chain, spot, width)
                if _shown(old_legs) != _shown(new_legs):
                    different.append((cycle.expiry, new.code, width, "legs"))
                    continue
                if new_legs is None:
                    continue
                if old_structures.payoff_bounds(old_legs) != payoff_bounds(new_legs):
                    different.append((cycle.expiry, new.code, width, "bounds"))
                prices = [leg_price(quotes.get(leg.contract), cycle.entry_day).price for leg in new_legs]
                if None not in prices:
                    compared += 1
                    if old_cost.max_loss(old_legs, prices) != new_cost.max_loss(new_legs, prices):
                        different.append((cycle.expiry, new.code, width, "max_loss"))
    assert different == [] and compared > 1000

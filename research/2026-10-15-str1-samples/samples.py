"""Story STR1 real-output samples (JUDGE.md quality rule 6), a dry run of the committed code: no post, no order, no
live data. Historical example only: the last discovery-period cycle in the NIFTY panel (entry-day closes only: no
exit or P&L is computed, since a new structure's outcome on spent history would be an unregistered trial), plus C4's
refusal of a planted naked short and a D2 candidate on the C4 test chain. Run: python
research/2026-10-15-str1-samples/samples.py > research/2026-10-15-str1-samples/output.txt"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from fno.composition import build_cycles, build_tradable_structures  # noqa: E402
from fno.config import load_app_config  # noqa: E402
from fno.research_data.panel_reader import read_nifty_panel  # noqa: E402
from fno.research_engine.cycle_costs import CycleTerms, PositionCosts  # noqa: E402
from fno.research_engine.cycles import cycle_rows  # noqa: E402
from fno.research_engine.leg_prices import contracts_on, leg_price  # noqa: E402
from fno.research_engine.structures import Leg, NakedShortLeg, payoff_bounds  # noqa: E402
from fno.storage.wiring import PANEL_FOLDER  # noqa: E402

WIDTHS = {"LC": 300.0, "LP": 300.0, "CDS": 200.0, "CCS": 200.0, "PDS": 200.0, "PCS": 200.0}


def b2_samples(cfg):
    panel = read_nifty_panel(PANEL_FOLDER, (2026,), cycle_rows)
    cycle = [c for c in build_cycles(panel) if c.has_entry_window and c.exit_day.isoformat() <= "2026-10-09"][-1]
    spot = panel.session_on(cycle.entry_day).underlying
    quotes = contracts_on(panel.options_on(cycle.entry_day, cycle.expiry))
    costs = PositionCosts(CycleTerms(lot=cfg["lot_sizes"]["NIFTY"], charges=cfg["charges"]))
    print(f"HISTORICAL EXAMPLE: entry {cycle.entry_day}, expiry {cycle.expiry}, exit {cycle.exit_day}, close {spot}")
    structures = {s.code: s for s in build_tradable_structures()}
    for code, width in WIDTHS.items():
        legs = structures[code].legs(frozenset(quotes), spot, width)
        prices = [leg_price(quotes.get(leg.contract), cycle.entry_day).price for leg in legs]
        shown = ", ".join(f"{'buy' if leg.bought else 'sell'} {leg.strike:g} {leg.kind} @ {p}" for leg, p in
                          zip(legs, prices, strict=True))  # fmt: skip
        low, high = payoff_bounds(legs)
        print(f"  {code} width {width:g}: {shown}; payoff bounds ({low:g}, {high:g}); "
              f"modelled max loss Rs {costs.max_loss(legs, prices):,.2f}")  # fmt: skip
    try:
        costs.max_loss([Leg(25_000.0, "CE", -1)], [100.0])
    except NakedShortLeg as refused:
        print(f"  B2 refusal: {refused}")


def c4_and_d2_samples():
    from tests.checks.test_validity_shapes import NAKED, ROWS
    from tests.checks.validity_builders import SPOT, check, committed_store
    from tests.checks.validity_proposal_builder import one_side_proposal
    from tests.checks.validity_sources import Margins
    from tests.playbook.test_one_side_codes import build

    print("C4 on the test chain (spot 25,000, 14 Oct 2026 fixture):")
    for name in ("a short call called LC", "a short call over a bought put called CCS"):
        code, spec, width = NAKED[name]
        report = check(one_side_proposal(code, spec, width, claimed_max_loss=1.0), store=committed_store(spot=SPOT),
                       margins=Margins(ROWS))  # fmt: skip
        for r in report.failures:
            if r.name in ("bounded_loss", "shape"):
                print(f"  {name}: FAIL {r.name}: {r.reason}")
    print("D2 candidate on the evaluation test chain (spot 25,000):")
    for code in ("PCS", "LC"):
        c = build(code, [300, 200, 100])
        legs = ", ".join(f"{'buy' if p.leg.bought else 'sell'} {p.contract}" for p in c.proposal.legs)
        print(f"  {code}: width {c.proposal.terms.width:g}: {legs}; max loss Rs {c.max_loss:,.2f}; score {c.score:.4f}")


if __name__ == "__main__":
    b2_samples(load_app_config())
    c4_and_d2_samples()

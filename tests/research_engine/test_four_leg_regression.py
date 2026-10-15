"""Story STR1 criterion 9: opening `Structure` to any number of legs leaves experiment 1's four-leg results unchanged.
Every discovery-period cycle (2024-26, 33 cycles x SF, SC, BF) re-simulated with today's code equals the published
`results_discovery.json` field by field: status, width, gross, charges, pads, net, maximum loss and the
impossible-exit flag. Reads only discovery years (the challenge years stay with the frozen worktree)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from fno.composition import build_cycle_simulator, build_cycles, build_structures
from fno.config import load_app_config
from fno.research_data.panel_reader import read_nifty_panel
from fno.research_engine.cycles import cycle_rows
from fno.storage.wiring import PANEL_FOLDER

RESULTS = Path(__file__).resolve().parents[2] / "research" / "2026-10-12-experiment-1" / "results_discovery.json"
FIELDS = ("status", "width", "gross", "charges", "pads", "net", "max_loss", "exit_outside_payoff")


@pytest.fixture(scope="module")
def recomputed():
    panel = read_nifty_panel(PANEL_FOLDER, (2024, 2025, 2026), cycle_rows)
    simulator = build_cycle_simulator(load_app_config(), panel)
    cycles = {c.expiry.isoformat(): c for c in build_cycles(panel)}
    published = json.loads(RESULTS.read_text(encoding="utf-8"))["opportunities"]
    return [
        (o["cycle"]["expiry"], code, o["structures"][code], simulator.simulate(cycles[o["cycle"]["expiry"]], s))
        for o in published
        for code, s in ((s.code, s) for s in build_structures())
    ]


def test_all_99_published_four_leg_results_are_recomputed(recomputed):
    assert len(recomputed) == 99


def test_every_four_leg_result_equals_the_published_one(recomputed):
    different = []
    for expiry, code, published, result in recomputed:
        now = {"status": str(result.status), "width": result.width, "gross": result.gross, "charges": result.charges,
               "pads": result.pads, "net": result.net, "max_loss": result.max_loss,
               "exit_outside_payoff": result.exit_outside_payoff}  # fmt: skip
        for field in FIELDS:
            if now[field] != pytest.approx(published[field], abs=1e-6):
                different.append((expiry, code, field, published[field], now[field]))
    assert different == []

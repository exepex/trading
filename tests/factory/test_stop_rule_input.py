"""Test B's R1 input (story R1c, the F8/BG1 owner's design, 16 Oct 2026): present only once a shadow is registered (G4),
never because the gate log merely exists, as today's log holds G0 rows only."""

from fno.budget.stop_rule_tracker import INPUTS
from fno.factory.constants import GATES_FILE
from fno.factory.gate_log import GateRow
from fno.factory.wiring import build_gate_log

from .helpers import init_repo


def test_the_r1_input_needs_a_registered_shadow(tmp_path):
    init_repo(tmp_path)
    [r1] = [i for i in INPUTS if i.story == "R1"]
    assert r1.path == GATES_FILE and not r1.exists(tmp_path)
    gates = build_gate_log(tmp_path)
    gates.append(GateRow("2", "G0", "idea", "2026-10-17", "abc", ""))
    assert (tmp_path / GATES_FILE).exists() and not r1.exists(tmp_path)  # G0 rows only: still missing
    numbers = "version=x1-sc-v1;sample=11;pass_level=0.05;min_net=150;question=q"
    gates.append(GateRow("2", "G4", "registered", "2026-10-17", "abc", numbers))
    assert r1.exists(tmp_path)

"""R1c (S1 owner's condition, 16 Oct 2026): `fno/factory/constants.py` is not hashed as a whole (it holds G1-G3's
numbers too), so every value a hashed module imports from it is pinned here. These values decide which gate-log rows
are read and which shadows the stop rule's Test B counts, so changing one after the freeze fails here."""

import ast
from pathlib import Path

from fno.config import ROOT
from fno.evaluation.freeze import frozen_targets
from fno.evaluation.protocol import PROTOCOL_FILE
from fno.factory import constants

FACTORY_CONSTANTS = "fno.factory.constants"
PINNED = {
    "GATES_FILE": "research/factory/gates.csv",
    "GATE_COLUMNS": ("trial_id", "gate", "outcome", "on", "commit", "numbers"),
    "NUMBERS_PATTERN": r"^([a-z_0-9]+=[^;,=\s]+(;[a-z_0-9]+=[^;,=\s]+)*)?$",
    "GATE_OUTCOMES": {
        "G0": ("idea",),
        "G1": ("passed", "screened_out"),
        "G2": ("fresh", "exploratory"),
        "G3": ("planned", "exploratory_shadow"),
        "G4": ("registered",),
        "G6": ("passed", "failed"),
    },  # fmt: skip
    "Gate": {
        "IDEA_CARD": "G0",
        "SCREEN": "G1",
        "DATA_SPEND": "G2",
        "SAMPLE_PLAN": "G3",
        "REGISTRATION": "G4",
        "VERDICT": "G6",
    },  # fmt: skip
}


def names_imported_by_hashed_modules() -> set[str]:
    found = set()
    for target in frozen_targets((ROOT / PROTOCOL_FILE).read_text(encoding="utf-8")):
        if not target.endswith(".py"):
            continue
        package = Path(target).parent.parts
        for node in ast.walk(ast.parse((ROOT / target).read_text(encoding="utf-8"))):
            if isinstance(node, ast.ImportFrom):
                base = list(package[: len(package) - node.level + 1] if node.level else ())
                if ".".join(base + (node.module.split(".") if node.module else [])) == FACTORY_CONSTANTS:
                    found |= {alias.name for alias in node.names}
    return found


def current(name: str):
    value = getattr(constants, name)
    if name == "Gate":
        return {member.name: member.value for member in value}
    if name == "GATE_OUTCOMES":
        return {str(gate): tuple(str(o) for o in outcomes) for gate, outcomes in value.items()}
    return value


def test_every_value_a_hashed_module_imports_from_the_factory_constants_is_pinned():
    assert names_imported_by_hashed_modules() - set(PINNED) == set()


def test_each_pinned_value_is_unchanged():
    for name, value in PINNED.items():
        assert current(name) == value, name

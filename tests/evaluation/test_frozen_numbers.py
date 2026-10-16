"""S1 item 15, judge 229 addendum 1: `fno/constants.py` is not hashed as a whole (it holds names and enum values that
change for every story), so every number a hashed module imports from it is pinned here to the frozen protocol text.
Changing one alone, or a hashed module importing a new unpinned number, fails before a freeze."""

import ast
from pathlib import Path

import fno.constants as constants
from fno.config import ROOT
from fno.evaluation.freeze import frozen_targets
from fno.evaluation.protocol import PROTOCOL_FILE, parse_protocol

PINNED = {  # constant -> (protocol item, its words with the number)
    "PAPER_GATE_MONTHS": ("paper_gate", "at least {} full calendar months"),
    "UNPROVEN_BELOW_COMPLETED_TRADES": ("paper_gate", "at least {} completed positions"),
}


def text() -> str:
    return (ROOT / PROTOCOL_FILE).read_text(encoding="utf-8")


def numbers_imported_by_hashed_modules() -> dict[str, set[str]]:
    found: dict[str, set[str]] = {}
    for target in frozen_targets(text()):
        if not target.endswith(".py"):
            continue
        package = Path(target).parent.parts
        for node in ast.walk(ast.parse((ROOT / target).read_text(encoding="utf-8"))):
            if not isinstance(node, ast.ImportFrom):
                continue
            base = list(package[: len(package) - node.level + 1] if node.level else ())
            if ".".join(base + (node.module.split(".") if node.module else [])) != "fno.constants":
                continue
            for alias in node.names:
                value = getattr(constants, alias.name, None)
                if isinstance(value, int | float) and not isinstance(value, bool):
                    found.setdefault(alias.name, set()).add(target)
    return found


def test_every_number_a_hashed_module_imports_from_constants_is_pinned():
    assert set(numbers_imported_by_hashed_modules()) - set(PINNED) == set()


def test_each_pinned_number_is_the_one_the_protocol_states():
    items = parse_protocol(text()).items
    for name, (item, words) in PINNED.items():
        assert words.format(getattr(constants, name)) in items[item].value, name

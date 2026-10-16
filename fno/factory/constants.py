"""The factory's fixed names (story R1), used only by `fno/factory/`: module-specific constants (CLAUDE.md), kept out
of `fno/constants.py`, which is at the 350-line limit."""

from enum import StrEnum

IDEAS_FOLDER = "research/ideas"
TEMPLATE_CARD = "TEMPLATE.md"
GATES_FILE = "research/factory/gates.csv"
GATE_COLUMNS = ("trial_id", "gate", "outcome", "on", "commit", "numbers")
CARD_FENCE = "factory"  # the card's machine block: a fenced ```factory YAML block
IDEA_KIND = "prospective"  # every factory idea is registered before any of its results exists
BACKFILLED = "backfilled=yes"  # a G0 row written by R1a for a card registered by hand before the code
NUMBERS_PATTERN = r"^([a-z_0-9]+=[^;,=\s]+(;[a-z_0-9]+=[^;,=\s]+)*)?$"  # k=v;k=v, or empty
DEFAULT_ALPHA = 0.01  # FACTORY_RULES section 5's example level (1% one-sided)


class Gate(StrEnum):
    IDEA_CARD = "G0"


class Outcome(StrEnum):
    IDEA = "idea"

"""The machine-readable trade of a playbook version (story D2 needs it from the file): which structure, which wing
widths to try, how many lots, and which expiry is an opportunity on which day. The text fields beside them
(`strikes_rule`, `width_rule`, `size_rule`) describe the same rule for people."""

from __future__ import annotations

from dataclasses import dataclass

from ..constants import EXPIRY_MONTHLY
from .fields import Fields
from .vocabulary import STRUCTURE_CODES

STRUCTURE = ("code", "strikes_rule", "width_rule", "widths", "lots", "expiry")
EXPIRY = ("kind", "min_days", "max_days", "exit_days_before_expiry")


@dataclass(frozen=True)
class ExpiryRule:
    """An opportunity is the first trading day on which an expiry of `kind` is `min_days` to `max_days` calendar days
    away (experiment 1's decision day); the time exit is the last trading day at least `exit_days_before_expiry`
    calendar days before the expiry."""

    kind: str
    min_days: int
    max_days: int
    exit_days_before_expiry: int


@dataclass(frozen=True)
class StructureSpec:
    code: str  # SF, SC or BF: the code fixes the body strikes (research_engine/structures.py)
    strikes_rule: str
    width_rule: str
    widths: tuple[float, ...]  # wing widths in points, widest first; the desk keeps the widest within the loss cap
    lots: int
    expiry: ExpiryRule


def parse_structure(fields: Fields) -> StructureSpec:
    return StructureSpec(
        code=fields.choice("code", STRUCTURE_CODES),
        strikes_rule=fields.text("strikes_rule"),
        width_rule=fields.text("width_rule"),
        widths=_widths(fields),
        lots=fields.whole("lots", 1),
        expiry=_expiry(fields.section("expiry", EXPIRY)),
    )


def _widths(fields: Fields) -> tuple[float, ...]:
    values = fields.raw("widths")
    numbers = isinstance(values, list) and all(isinstance(v, int | float) and not isinstance(v, bool) for v in values)
    if not numbers or not values or list(values) != sorted(set(values), reverse=True) or min(values) <= 0:
        raise fields.refuse("widths", "must be positive point widths, widest first, no repeats")
    return tuple(float(v) for v in values)


def _expiry(fields: Fields) -> ExpiryRule:
    rule = ExpiryRule(
        kind=fields.choice("kind", (EXPIRY_MONTHLY,)),
        min_days=fields.whole("min_days", 1),
        max_days=fields.whole("max_days", 1),
        exit_days_before_expiry=fields.whole("exit_days_before_expiry", 0),
    )
    if rule.max_days < rule.min_days:
        raise fields.refuse("max_days", "must not be below min_days")
    if rule.exit_days_before_expiry >= rule.min_days:
        raise fields.refuse("exit_days_before_expiry", "must be below min_days, so entry comes before the exit")
    return rule

"""What scoreboard B takes from the committed D3 record that opened a trade (story S2): its maximum loss at entry (the
risk at stake while it is open), C2's stressed margin and stress usage at entry, whether the owner overrode it (read
through the `OwnerOverrides` port) and its D6 segment."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import date

from ..books.versions import Segment

MARGIN_RULE, STRESS_RULE = "margin_room", "stress_loss"


@dataclass(frozen=True)
class EntryFacts:
    decision_id: str  # D6's ID: `<run_id>/<opportunity_id>`
    day: date
    max_loss: float  # rupees, the trade's modelled maximum loss at entry (D3's `expected.worst_rs`)
    stressed_margin: float | None  # rupees, C2's stressed margin of this trade at entry
    stress_usage: float | None  # C2's worst stress loss of the book with this trade, as a share of its limit
    overridden: bool
    segment: Segment


def _verdict(record: Mapping, rule: str) -> Mapping | None:
    risk = record.get("risk") or {}
    return next((v for v in risk.get("verdicts", ()) if v["rule"] == rule), None)


def entry_facts(record: Mapping, segment: Segment, overridden: bool) -> EntryFacts:
    """The facts of a chosen trade's record; a record without a maximum loss is refused (it cannot have been
    traded)."""
    worst = (record.get("expected") or {}).get("worst_rs")
    if worst is None:
        raise ValueError(f"{record['run_id']}/{record['opportunity_id']}: no maximum loss at entry in the record")
    margin, stress = _verdict(record, MARGIN_RULE), _verdict(record, STRESS_RULE)
    trade_id = (record.get("risk") or {}).get("trade_id")
    stressed = margin["numbers"]["stressed_margin_rs"].get(trade_id) if margin else None
    usage = stress["numbers"]["worst_loss_rs"] / stress["numbers"]["limit_rs"] if stress else None
    return EntryFacts(
        f"{record['run_id']}/{record['opportunity_id']}", date.fromisoformat(record["run_id"][:10]), -float(worst),
        stressed, usage, overridden, segment,
    )  # fmt: skip

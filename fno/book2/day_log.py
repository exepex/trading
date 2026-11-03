"""Book 2's day log (story F5): the answer's reason for the day; each slot with its envelope verdict, what was picked,
any shadow-only choice and the rule's own would-be trade; every pick that could not trade; and, when the judge
blocked, the rule default kept as a shadow. Canonical JSON, written once per day under `journal/book2_hybrid/ai_days/`,
committed with the day's run."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import date
from pathlib import Path

from ..book3.json_files import write_new_json
from ..constants import BOOK2_HYBRID, JOURNAL_FOLDER
from ..playbook.selection import Attempt
from .slots import Default, SlotResult, terms_json

LOG_FOLDER = f"{JOURNAL_FOLDER}/{BOOK2_HYBRID}/ai_days"
KIND, SCHEMA_VERSION = "book2_day_log", 1


def log_path(day: date) -> str:
    return f"{LOG_FOLDER}/{day.isoformat()}.json"


def write_day_log(root: Path, day: date, reason: str, slots: Sequence[SlotResult], attempted: Sequence[Attempt],
                  judge_blocked: Sequence[Default] | None, rule_trades: Mapping[str, dict]) -> Path:  # fmt: skip
    """`judge_blocked`: the rule defaults kept as a shadow when the judge's verdict blocked (None: it did not).
    `rule_trades`: each default's trade as the sheet built it (legs, width, lots, maximum loss): the rule's would-be
    proposal, so a vetoed or blocked default can be priced later from the day's recorded quotes even on a day the
    version's D2 shadow book did not trade it (its own one-open-trade limit; orchestrator's ruling, 25 Oct)."""
    shadow = None if judge_blocked is None else [{"opportunity_id": d.opportunity_id, **terms_json(d.terms),
                                                   "rule_trade": rule_trades.get(d.opportunity_id)}
                                                  for d in judge_blocked]  # fmt: skip
    attempts = [{**a.pick.to_json(), "why": a.why} for a in attempted]
    slot_records = [{**s.record(), "rule_trade": rule_trades.get(s.default.opportunity_id)} for s in slots]
    body = {"kind": KIND, "schema_version": SCHEMA_VERSION, "day": day.isoformat(), "reason": reason,
            "slots": slot_records, "attempted_picks": attempts, "judge_blocked_rule_default": shadow}  # fmt: skip
    return write_new_json(Path(root) / log_path(day), body)

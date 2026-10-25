"""Book 3's matched shadow decisions of a day (story F7): one entry per common opportunity (E2's common pack, without
its `no_trade` entry), each a take at a width from that version's own set (one lot, scoreboard A's unit) or
`no_trade`: D4's `BookTerms(version, width, 1)` or `None`. Code writes `no_decision`, with the reason, for every
opportunity the answer left out, answered twice or answered with a width outside the set; an answered ID that is not
a common opportunity is dropped and listed in `refused`. Book 3 has no envelope: it may take an opportunity whose rule
did not fire. The file is canonical JSON, written once, and never read by the fill path: a shadow never touches the
account."""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from datetime import date
from pathlib import Path

from ..constants import BOOK3_AI, JOURNAL_FOLDER
from ..desk.opportunity_set import NO_TRADE_OPPORTUNITY
from ..playbook.schema import version_id
from .json_files import write_new_json

SHADOW_FOLDER = f"{JOURNAL_FOLDER}/{BOOK3_AI}/shadow"
KIND, SCHEMA_VERSION = "book3_shadow_decisions", 1
TAKE, NO_TRADE, NO_DECISION = "take", "no_trade", "no_decision"
MISSING = "no shadow entry in the answer"
OUTSIDE = "width {width:g} is not in {version}'s set {widths}"
NO_VERSION = "the version's widths cannot be read"
UNKNOWN = "not a common opportunity today"
TWICE = "answered twice: which entry counts is not decidable"

Widths = Callable[[str, int], Sequence[float] | None]  # (playbook name, version) -> its widths, None if unknown


def shadow_path(day: date) -> str:
    return f"{SHADOW_FOLDER}/{day.isoformat()}.json"


def shadow_body(day: date, common_pack_sha256: str, opportunities: Sequence[Mapping], answered: Sequence[Mapping],
                widths: Widths) -> dict:  # fmt: skip
    common = [o for o in opportunities if o["opportunity_id"] != NO_TRADE_OPPORTUNITY["opportunity_id"]]
    known = {o["opportunity_id"] for o in common}
    by_id = {a["opportunity_id"]: a for a in reversed(answered)}
    twice = {i for i in by_id if sum(a["opportunity_id"] == i for a in answered) > 1}
    entries = [_duplicate(o) if o["opportunity_id"] in twice else _entry(o, by_id.get(o["opportunity_id"]), widths)
               for o in common]  # fmt: skip
    refused = [{"opportunity_id": i, "why": UNKNOWN} for i in sorted(by_id) if i not in known]
    return {"kind": KIND, "schema_version": SCHEMA_VERSION, "day": day.isoformat(),
            "common_pack_sha256": common_pack_sha256, "entries": entries, "refused": refused}  # fmt: skip


def _base(opportunity: Mapping) -> dict:
    return {"opportunity_id": opportunity["opportunity_id"], "strategy": opportunity["strategy"],
            "version": opportunity["version"]}  # fmt: skip


def _duplicate(opportunity: Mapping) -> dict:
    return {**_base(opportunity), "action": NO_DECISION, "width": None, "reason": TWICE}


def _entry(opportunity: Mapping, answer: Mapping | None, widths: Widths) -> dict:
    base = _base(opportunity)
    if answer is None:
        return {**base, "action": NO_DECISION, "width": None, "reason": MISSING}
    if answer["action"] == NO_TRADE:
        return {**base, "action": NO_TRADE, "width": None, "reason": answer["reason"]}
    allowed = widths(opportunity["strategy"], opportunity["version"])
    if allowed is None:
        return {**base, "action": NO_DECISION, "width": None, "reason": NO_VERSION}
    if float(answer["width"]) not in [float(w) for w in allowed]:
        name = version_id(opportunity["strategy"], opportunity["version"])
        why = OUTSIDE.format(width=float(answer["width"]), version=name, widths=list(allowed))
        return {**base, "action": NO_DECISION, "width": None, "reason": why}
    return {**base, "action": TAKE, "width": float(answer["width"]), "reason": answer["reason"]}


def write_shadow(root: Path, body: dict) -> Path:
    return write_new_json(Path(root) / shadow_path(date.fromisoformat(body["day"])), body)

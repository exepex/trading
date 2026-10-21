"""Story G11, the AI books' v4 rows: each book-day becomes one G7-schema row per started v4 question in G8's folder
(`research/forecasts/v4/<book>/<question>.csv`), and every failed run is a miss, never a gap.

- **The status is F1's gate, used as is** (`scoring_gate.scoring_status`, the one rule every AI reader calls): scored
  is `ok` with the book's value; an unscored day keeps its outcome's own name (late, not_fired, no_submission,
  not_revealed, invalid, model_mismatch, exposed); a transcript breach is `breach`; a day the stop rule kept from
  firing is `stopped`. A pending day (audit due, week not drawn, not collected) gets **no row**: a written row never
  changes, so it waits, and G8's look refuses while any slot-day has none (the A16/G8 builder's reconciliation).
- **One row per started question,** the same list the rules slot answers that day (passed in, never an AI list).
- **The row** is G7's own (`records.record`, its range checks reused), with the book's registered version in
  `forecaster_version`, `label=live` (AI answers have no back-fill), `kind=ai`, the book's slot, the prompt's hash in
  `method_sha256` and the book's own inputs' hash in `inputs_sha256`. Written once (`records.write`)."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace
from datetime import date
from pathlib import Path

from ..constants import BOOK2_HYBRID, BOOK3_AI, V4_SLOT_AI, V4_SLOT_HYBRID
from ..forecast_v4_rules import records
from ..forecast_v4_rules.baselines import OK
from .outcome import EXPOSED, INVALID, LATE, MODEL_MISMATCH, NO_SUBMISSION, NOT_FIRED, NOT_REVEALED
from .scoring_gate import PENDING, SCORED, ScoringStatus
from .stop_rule import STOPPED as STOP_RULE_REASON

AI_KIND = "ai"
SLOTS = {BOOK2_HYBRID: V4_SLOT_HYBRID, BOOK3_AI: V4_SLOT_AI}
BREACH, STOPPED = "breach", "stopped"
OUTCOME_MISSES = (LATE, NOT_FIRED, NO_SUBMISSION, NOT_REVEALED, INVALID, MODEL_MISMATCH, EXPOSED)
TRANSCRIPT_BREACH = "transcript breach"  # the gate's reason for a breach found by the transcript audit
STOPPED_MARK = STOP_RULE_REASON.partition("{")[0]  # "stopped: ", how the stop rule's reason starts
UNKNOWN_OUTCOME = "{book} {day}: outcome {reason!r} has no v4 status; nothing is written (never a guessed status)"


@dataclass(frozen=True)
class BookDay:
    """What the collection settled for one book on one day: the gate's answer, the audit's notes, the values the book
    revealed per question (None where it gave none) and its version's hashes."""

    book: str
    day: date
    gate: ScoringStatus
    notes: Sequence[str]
    values: Mapping[str, float | None]
    version: str  # the registered label, e.g. book3_ai/v2/sha256:.../isolation:sealed_same_day
    method_sha256: str  # the prompt's
    inputs_sha256: str  # the book's own inputs (its pointer)
    made_at: str


def v4_status(day: BookDay) -> str | None:
    """The day's v4 status, or None while its gate is pending (no row yet)."""
    gate = day.gate
    if gate.status == PENDING:
        return None
    if gate.status == SCORED:
        return OK
    if gate.reason.startswith(TRANSCRIPT_BREACH):
        return BREACH
    if gate.reason == NOT_FIRED and any(STOPPED_MARK in note for note in day.notes):
        return STOPPED
    if gate.reason in OUTCOME_MISSES:
        return gate.reason
    raise ValueError(UNKNOWN_OUTCOME.format(book=day.book, day=day.day, reason=gate.reason))


def v4_rows(day: BookDay, questions: Sequence[str]) -> list[records.Record]:
    """One row per started question; empty while the gate is pending. A scored day without a value for a question is
    that question's `invalid` row (the book answered, but not this question)."""
    status = v4_status(day)
    if status is None:
        return []
    audit = dict(label=records.LIVE, kind=AI_KIND, slot=SLOTS[day.book], method_sha256=day.method_sha256,
                 inputs_sha256=day.inputs_sha256, made_at=day.made_at)  # fmt: skip
    rows = []
    for question in questions:
        value = day.values.get(question) if status == OK else None
        own = status if status != OK or value is not None else INVALID
        row = records.record(day.day, question, own, value, **audit)
        rows.append(replace(row, forecaster_version=day.version))
    return rows


def write_book_day(folder: Path, day: BookDay, questions: Sequence[str]) -> int:
    """The day's rows written once in the book's own folder; the number added (0 while pending, or already written)."""
    rows = v4_rows(day, questions)
    if not rows:
        return 0
    return sum(records.write(folder, day.book, question, [row]) for question, row in zip(questions, rows, strict=True))

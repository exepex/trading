"""Story G11, collecting the AI books' v4 day (response 272), run in forecast-capture's collect slot after the 15:10
deadline and its reveals: for each book, read its submission at v4's paths with GitHub's receipt times, rebuild its
input from the Drive pack and require the same hash the fire logged, judge it with F1/G5's own `outcome.judge` under
v4's terms (15:10, reveal 15:10:10-15:30), mark exposures, and write its audit file once. The rows come later, from
the settled audit (`v4_settle.py`): a written row never changes, so it waits for the transcript audit.

- A session the fire never ran (no fire log, a released pack, from the v4 go-live date) is collected as `not_fired`
  for every registered question, so it is a miss, never a gap (design item 7).
- No released pack: nothing is collected (no row; the look's reconciliation leaves `system_late` days out).
- The release record is read here, never taken from the fire log: its SHA is stored in the audit, and the rows' pack
  guard checks the pack each book was given against it (two sources, not one).
- **Every session since go-live still without both audits is collected again** (G11 C19): a day whose GitHub receipt
  time cannot be found yet (`ReceiptUnknown`) gets no verdict and no audit (never a guessed time; exposure needs both
  books' times, so the whole day waits), is printed "awaiting GitHub's receipt" and is retried by every later collect;
  a session the collect itself never ran is caught up the same way. G8's look refuses while such a day has no row."""

from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path

from ..constants import AI_BOOKS, FORECAST_PROTOCOL_V4
from ..v4_pack.model import Pack
from ..v4_pack.release import NotReleased, ReleasedPacks
from .history import RepoHistory
from .outcome import INVALID, NOT_FIRED, Outcome, judge, mark_exposures
from .receipts import PushReceipts, ReceiptUnknown
from .record_writer import audit_text
from .run_terms import V4_TERMS
from .submissions import read_submission
from .v4_book_inputs import QuestionsRefused, V4BookInputs
from .v4_input import input_sha256
from .v4_pointer import v4_envelope, v4_labels
from .versions import current_version, version_by_label

LINE = "Omenix F&O AI forecasts v4 (GitHub Actions): {day}: {result}"
AWAITING_RECEIPT = "awaiting GitHub's receipt ({why}); nothing written, the next collect retries it"
NEVER_RAN = "the v4 fire never ran this session"
NOT_REBUILT = "the input could not be rebuilt to the hash the fire logged ({why})"


@dataclass
class V4BookCollector:
    root: Path
    history: RepoHistory
    receipts: PushReceipts
    inputs: V4BookInputs
    released: Callable[[], ReleasedPacks]
    clock: Callable[[], datetime]
    live_from: date | None
    sessions: Callable[[date, date], list[date]]  # v4's scored sessions from the first day to the last, both included

    def collect(self, day: date) -> list[str]:
        if self.live_from is None or day < self.live_from:
            return [LINE.format(day=day, result="v4 is not live yet; nothing collected")]
        days = [d for d in self.sessions(self.live_from, day) if d == day or not self._collected(d)]
        return [line for d in days for line in self._collect_day(d)]

    def _collected(self, day: date) -> bool:
        return all((self.root / V4_TERMS.audit_path(day, book)).is_file() for book in AI_BOOKS)

    def _collect_day(self, day: date) -> list[str]:
        try:
            packs = self.released()
            release = packs.release(day)
            pack = packs.pack(release)
        except NotReleased as missing:
            return [LINE.format(day=day, result=f"no released pack ({missing}); nothing collected (no row)")]
        log = self._log(day, release.pack_sha256)
        try:
            outcomes = {book: self._outcome(day, book, entry, pack) for book, entry in log["books"].items()}
        except ReceiptUnknown as unknown:
            return [LINE.format(day=day, result=AWAITING_RECEIPT.format(why=unknown))]
        mark_exposures(outcomes)
        lines = []
        for book, outcome in outcomes.items():
            written = self._write(day, outcome, log["books"][book], release.pack_sha256)
            lines.append(LINE.format(day=day, result=f"{book} {outcome.status}: {written}"))
        return lines

    def _log(self, day: date, released_sha256: str) -> dict:
        """The fire log; a session the fire never ran, or ran while no pack could be read, gets one built here: every
        book not_fired, so a released day is never left without a row."""
        file = self.root / V4_TERMS.fired_path(day)
        log = json.loads(file.read_text(encoding="utf-8")) if file.is_file() else {}
        if "books" in log:
            return log
        return {"books": {book: self._never_ran(day, book, released_sha256) for book in AI_BOOKS}}

    def _never_ran(self, day: date, book: str, sha: str) -> dict:
        version = current_version(book, FORECAST_PROTOCOL_V4)
        try:
            questions = self.inputs.questions(version, day)
        except QuestionsRefused as wrong:
            return {"version": version.label, "fired": False, "stop_rule": False, "pack_sha256": sha,
                    "questions": [], "reason": str(wrong)}  # fmt: skip
        return {"version": version.label, "fired": False, "stop_rule": False, "pack_sha256": sha,
                "questions": questions, "reason": NEVER_RAN}  # fmt: skip

    def _outcome(self, day: date, book: str, entry: dict, pack: Pack) -> Outcome:
        version, questions = version_by_label(entry["version"]), tuple(entry.get("questions", ()))
        if not entry["fired"]:
            outcome = Outcome(book, NOT_FIRED, version.label, questions)
            outcome.withdraw(NOT_FIRED, f"the routine was not fired: {entry.get('reason', '')}")
            return outcome
        try:
            built = self.inputs.build(version, day, questions, pack, entry["pack_sha256"])
        except ValueError as broken:
            return _invalid(book, version.label, questions, NOT_REBUILT.format(why=broken))
        if input_sha256(built) != entry["input_sha256"]:
            return _invalid(book, version.label, questions, NOT_REBUILT.format(why="another hash"))
        submission = read_submission(self.history, self.receipts, day, book, V4_TERMS)
        unknown = [p.receipt_problem for p in (submission.commitment, submission.reveal) if p and p.received_at is None]
        if unknown:
            raise ReceiptUnknown(unknown[0])
        return judge(book, day, submission, v4_labels(built), v4_envelope(built), version, V4_TERMS, questions)

    def _write(self, day: date, outcome: Outcome, fired: dict, released_sha256: str) -> str:
        """Once; the release record's SHA, read here and not from the fire log, is what the rows' pack guard checks."""
        file = self.root / V4_TERMS.audit_path(day, outcome.book)
        if file.is_file():
            return "already collected (the first collection stands)"
        file.parent.mkdir(parents=True, exist_ok=True)
        v4 = {"collected_at": self.clock().isoformat(), "released_sha256": released_sha256}
        file.write_text(audit_text(day, outcome, fired, v4), encoding="utf-8")
        return "collected; its rows land once its audit settles"


def _invalid(book: str, label: str, questions: tuple[str, ...], why: str) -> Outcome:
    outcome = Outcome(book, INVALID, label, questions)
    outcome.withdraw(INVALID, why)
    return outcome

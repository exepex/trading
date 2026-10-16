"""The collection (story F1t, O1's `ai_collect` step): after Book 1 decides, for each live AI book, read its sealed
submission with receipts from the remote observer's two readings, judge it (`outcome.judge`), hand an accepted answer
to its decider (`Promoter`) and write the day's outcome record. Returns every book's outcome and the files to commit
(the outcome records and each promoted run). A book with an outcome record already is never judged again."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from ..ai.fire_once import NOT_FIRED, FireOnceLog
from ..ai.history import RepoHistory
from ..ai.observed_receipts import ObservationFile, ObservedPushes
from ..ai.submissions import Submission, read_submission
from ..desk.common_pack import CommonPack
from ..desk.pack_items import canonical_json, sha256_hex
from ..desk.private_pack import ALLOWED_FOLDERS, PrivatePack
from .figures import private_figures, redact
from .outcome import ACCEPTED, PROMOTED, REFUSED, DayOutcome, Deadlines, Judged, judge, seen_at
from .paths import commitment_path, fired_path, observations_path, reveal_path
from .ports import AcceptedDecision, AnalystCards, DayPacks, consulted_units
from .promote import Promoter, Promotion
from .records import OutcomeRecords
from .versions import DecisionRegistry, VersionRefused

NO_ENTRY = "no fire log entry for the day"
PACKS_MISSING = "the day's packs could not be read: {why}"
FAILED = "the collection failed for this book: {error}"
PACKS_CHANGED = "the day's packs are not the ones fired (their SHA-256 differs from the fire log's labels)"
CARDS_CHANGED = "the analyst cards read now are not the ones fired (their SHA-256 differs)"


class PacksMissing(RuntimeError):
    """The day's committed common pack or the book's private pack is not on disk."""


@dataclass(frozen=True)
class Collected:
    outcomes: dict[str, dict]  # book -> its outcome record
    paths: tuple[Path, ...]


class DecisionCollector:
    def __init__(self, root: Path, history: RepoHistory, registry: DecisionRegistry, promoter: Promoter,
                 packs: DayPacks, cards: AnalystCards, refresh: Callable[[], None]):  # fmt: skip
        self.root, self.history, self.registry, self.promoter = Path(root), history, registry, promoter
        self.packs, self.cards, self.refresh, self.records = packs, cards, refresh, OutcomeRecords(root)

    def collect(self, day: date, books: Sequence[str], deadlines: Deadlines) -> Collected:
        self.refresh()
        receipts = ObservedPushes(ObservationFile(self.root / observations_path(day)).read(), self.history)
        fired = FireOnceLog(self.root, fired_path(day), lambda paths, message: None, lambda: None).read()
        pending = [book for book in books if not self.records.exists(day, book)]
        submissions = {book: self._submission(day, book, receipts) for book in pending}
        early = {book for book, sent in submissions.items() if isinstance(sent, Submission) and sent.reveal
                 and seen_at(receipts, sent.reveal.commit) == deadlines.receipt}  # fmt: skip
        paths: list[Path] = []
        for book in pending:  # one book's failure is that book's `refused` record, never another book's loss
            entry = fired.get(book, {"state": NOT_FIRED, "reason": NO_ENTRY})
            try:
                if not isinstance(submissions[book], Submission):
                    raise submissions[book]
                paths += self._one(day, book, entry, submissions[book], receipts, deadlines, sorted(early - {book}))
            except Exception as failure:  # noqa: BLE001 - recorded with its reason and named in the step's alert
                outcome = DayOutcome(book, REFUSED, FAILED.format(error=f"{type(failure).__name__}: {failure}"),
                                     entry.get("labels", {}).get("version", ""))  # fmt: skip
                paths.append(self.records.write(day, outcome, entry.get("labels", {}), ()))
        return Collected({book: self.records.read(day, book) for book in books}, tuple(paths))

    def _submission(self, day: date, book: str, receipts) -> Submission | Exception:
        try:
            return read_submission(self.history, receipts, day, book, commitment_path, reveal_path)
        except Exception as failure:  # noqa: BLE001 - becomes that book's refused record
            return failure

    def _one(self, day, book, entry, submission, receipts, deadlines, others) -> list[Path]:
        labels = entry.get("labels", {})
        try:
            facts = self._facts(day, book, entry, labels, submission)
        except (VersionRefused, PacksMissing) as missing:
            outcome = DayOutcome(book, ACCEPTED, version=labels.get("version", ""))
            facts, outcome = None, outcome.stop(REFUSED, PACKS_MISSING.format(why=missing))
        if facts is not None:
            outcome = judge(book, facts, receipts, deadlines, others)
        cards = self._cards(day, outcome, labels) if outcome.status == ACCEPTED else {}
        promotion = self._promote(day, book, entry, outcome, cards) if outcome.status == ACCEPTED else None
        outcome.reason = redact(outcome.reason, facts.private if facts else set())  # public record and alert
        written = self.records.write(day, outcome, labels, consulted_units(cards), promotion)
        return [written, *(promotion.paths if promotion else ())]

    def _facts(self, day, book, entry, labels, submission) -> Judged | None:
        if entry.get("state") == NOT_FIRED:
            return Judged(entry, labels, submission, lambda d: [], set(), "")
        version = self.registry.by_label(labels.get("version", ""))
        common, private = self._packs(day, book, labels)
        public = [folder for folder in ALLOWED_FOLDERS[book] if not folder.startswith("journal/")]
        figures = private_figures(private.body, common.data.decode("utf-8"), public)
        return Judged(entry, labels, submission, version.shape_check, figures, version.registered_model)

    def _promote(self, day, book, entry, outcome: DayOutcome, cards: dict) -> Promotion:
        version = self.registry.by_label(outcome.version)
        common, private = self._packs(day, book, entry.get("labels", {}))
        accepted = AcceptedDecision(
            book, day, version.label, version.registered_model, outcome.model_reported, entry.get("session", ""),
            common, private, outcome.answer.decision, cards, consulted_units(cards), outcome.commitment_commit,
            outcome.reveal_commit,
        )  # fmt: skip
        promotion = self.promoter.promote(accepted, version.write_paths)
        if promotion.promoted:
            outcome.status, outcome.reason = PROMOTED, f"run {promotion.run_id} committed for E3's deadline"
        else:
            outcome.stop(REFUSED, promotion.reason)
        return promotion

    def _cards(self, day: date, outcome: DayOutcome, labels: dict) -> dict:
        """F2's item read again (the fire log keeps only its hash): exactly the one fired, or the book is refused."""
        item = self.cards.item(day, self.registry.by_label(outcome.version).role_units)
        if sha256_hex(canonical_json(item)) != labels.get("cards_sha256"):
            outcome.stop(REFUSED, CARDS_CHANGED)
            return {}
        return item

    def _packs(self, day: date, book: str, labels: dict) -> tuple[CommonPack, PrivatePack]:
        """The packs exactly as fired: re-read, and refused when they are not what the book was given."""
        try:
            common, private = self.packs.common(day), self.packs.private(book, day)
        except (OSError, ValueError) as missing:
            raise PacksMissing(f"{type(missing).__name__}: {missing}") from None
        if (common.sha256, private.sha256) != (labels.get("common_pack_sha256"), labels.get("private_pack_sha256")):
            raise PacksMissing(PACKS_CHANGED)
        return common, private

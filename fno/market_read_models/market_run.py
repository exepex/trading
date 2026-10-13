"""One session's market read-model run (stories P6, P7): archive the session's files (when given a step for it), build
the rows, validate every block against the pinned W11 contract, publish all of them at once and read them back. Any
failure stops the run before anything is published, prints the reason and alerts #fno-desk; the previous publication
stays current. Every run leaves a run-status row: `running` at the start, then `published`, `failed` with a reason
code, or `skipped` (P7). It prints only counts and hashes, never a credential."""

from __future__ import annotations

from collections.abc import Callable
from datetime import date

from ..alerts.sender import AlertSender
from ..research_data.calendar import SessionCalendar
from .contract import ContractBroken, PinnedContract
from .publication import Publication, PublicationBuilder, hashes
from .publisher import PublishFailed, ReadModelPublisher
from .run_status import (
    ARCHIVE_INCOMPLETE,
    CONTRACT_CHANGED,
    CRASHED,
    FAILED,
    NOT_A_SESSION,
    PUBLISHED,
    READ_BACK_MISMATCH,
    SCHEMA_INVALID,
    SKIPPED,
    Outcome,
    RunStatusRecorder,
    database_code,
)  # fmt: skip
from .session_rows import IncompleteSession, SessionRowsBuilder

NOT_A_SESSION_LINE = "{day}: not a trading day, nothing to publish"
PUBLISHED_LINE = "{day}: published {count} blocks as {publication_id} to {publisher} ({added} rows added)"
READ_BACK = "read back {count} pages of {publication_id}: every payload SHA-256 equals the built records"
PAGE_HASH = "    {page_key} {sha256}"
READ_BACK_DIFFERS = "read back {publication_id}: {pages} differ from the built records"
FAILED_LINE = (
    "Omenix F&O market read models for {day} NOT published ({step}): {reason}. The previous publication stays current."
)
DAMAGED_PIN = "the pinned W11 contract copy differs from its pin: {files}"
CRASH_REASON = "the run stopped on an unexpected error; see its log"

Prepare = Callable[[date], str | None]  # archives the session's files; the first problem, or None


class Stopped(Exception):
    def __init__(self, step: str, code: str, reason: str):
        super().__init__(reason)
        self.step, self.code, self.reason = step, code, reason


class MarketRun:
    def __init__(
        self,
        calendar: SessionCalendar,
        contract: PinnedContract,
        rows: SessionRowsBuilder,
        publications: PublicationBuilder,
        publisher: ReadModelPublisher,
        alerts: AlertSender,
        status: RunStatusRecorder,
        run_id: Callable[[], str],
    ):
        self.calendar, self.contract, self.rows = calendar, contract, rows
        self.publications, self.publisher, self.alerts = publications, publisher, alerts
        self.status, self.run_id = status, run_id

    def run(self, day: date, prepare: Prepare | None = None) -> tuple[int, list[str]]:
        """(exit code, lines to print). The status row is written whatever happens; a crash is recorded, then raised."""
        run_id = self.run_id()
        notes = [self.status.start(run_id, day)]
        try:
            code, lines, outcome = self._attempt(day, prepare)
        except Exception:
            self.status.finish(run_id, Outcome(FAILED, CRASHED, CRASH_REASON))
            raise
        notes.append(self.status.finish(run_id, outcome))
        return code, lines + [note for note in notes if note]

    def _attempt(self, day: date, prepare: Prepare | None) -> tuple[int, list[str], Outcome]:
        if not self.calendar.is_session(day):
            line = NOT_A_SESSION_LINE.format(day=day)
            return 0, [line], Outcome(SKIPPED, NOT_A_SESSION, line)
        try:
            publication, added = self._publish(day, prepare)
        except Stopped as stop:
            message = FAILED_LINE.format(day=day, step=stop.step, reason=stop.reason)
            return 1, [message, self.alerts.send(message)], Outcome(FAILED, stop.code, message)
        line = PUBLISHED_LINE.format(day=day, count=len(publication.records), publication_id=publication.publication_id,
                                     publisher=self.publisher.name, added=added)  # fmt: skip
        pages = [PAGE_HASH.format(page_key=k, sha256=v) for k, v in sorted(hashes(publication).items())]
        read_back = READ_BACK.format(count=len(pages), publication_id=publication.publication_id)
        return 0, [line, read_back, *pages], Outcome(PUBLISHED, publication_id=publication.publication_id)

    def _publish(self, day: date, prepare: Prepare | None) -> tuple[Publication, int]:
        problem = prepare(day) if prepare else None
        if problem:
            raise Stopped("archived files", ARCHIVE_INCOMPLETE, problem)
        changed = self.contract.changed_files()
        if changed:
            raise Stopped("contract", CONTRACT_CHANGED, DAMAGED_PIN.format(files=", ".join(changed)))
        try:
            publication = self.publications.build(self.rows.build(day))
        except IncompleteSession as exc:
            raise Stopped("archived files", ARCHIVE_INCOMPLETE, str(exc)) from exc
        except ContractBroken as exc:
            raise Stopped("W11 schema", SCHEMA_INVALID, str(exc)) from exc
        try:
            added = self.publisher.publish(publication)
            stored = self.publisher.stored(publication.publication_id)
        except PublishFailed as exc:
            raise Stopped("publish", database_code(exc.failure_class), str(exc)) from exc
        built = hashes(publication)
        if stored != built:
            differing = sorted(k for k in built.keys() | stored.keys() if built.get(k) != stored.get(k))
            reason = READ_BACK_DIFFERS.format(publication_id=publication.publication_id, pages=", ".join(differing))
            raise Stopped("read-back", READ_BACK_MISMATCH, reason)
        return publication, added

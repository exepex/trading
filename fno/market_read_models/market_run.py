"""One session's market read-model run (story P6): build the rows from the archived files, validate every block against
the pinned W11 contract, publish all of them at once. Any failure stops the run before anything is published, prints
the reason and alerts #fno-desk; the previous publication stays current. Never publishes a partial session."""

from __future__ import annotations

from datetime import date

from ..alerts.sender import AlertSender
from ..research_data.calendar import SessionCalendar
from .contract import ContractBroken, PinnedContract
from .publication import PublicationBuilder
from .publisher import PublishFailed, ReadModelPublisher
from .session_rows import IncompleteSession, SessionRowsBuilder

NOT_A_SESSION = "{day}: not a trading day, nothing to publish"
PUBLISHED = "{day}: published {count} blocks as {publication_id} to {publisher}"
FAILED = (
    "Omenix F&O market read models for {day} NOT published ({step}): {reason}. The previous publication stays current."
)
DAMAGED_PIN = "the pinned W11 contract copy differs from its pin: {files}"


class MarketRun:
    def __init__(
        self,
        calendar: SessionCalendar,
        contract: PinnedContract,
        rows: SessionRowsBuilder,
        publications: PublicationBuilder,
        publisher: ReadModelPublisher,
        alerts: AlertSender,
    ):
        self.calendar, self.contract, self.rows = calendar, contract, rows
        self.publications, self.publisher, self.alerts = publications, publisher, alerts

    def run(self, day: date) -> tuple[int, list[str]]:
        """(exit code, lines to print)."""
        if not self.calendar.is_session(day):
            return 0, [NOT_A_SESSION.format(day=day)]
        changed = self.contract.changed_files()
        if changed:
            return self._failed(day, "contract", DAMAGED_PIN.format(files=", ".join(changed)))
        try:
            rows = self.rows.build(day)
        except IncompleteSession as exc:
            return self._failed(day, "archived files", str(exc))
        try:
            publication = self.publications.build(rows)
        except ContractBroken as exc:
            return self._failed(day, "W11 schema", str(exc))
        try:
            self.publisher.publish(publication)
        except PublishFailed as exc:
            return self._failed(day, "publish", str(exc))
        line = PUBLISHED.format(day=day, count=len(publication.records), publication_id=publication.publication_id,
                                publisher=self.publisher.name)  # fmt: skip
        return 0, [line]

    def _failed(self, day: date, step: str, reason: str) -> tuple[int, list[str]]:
        message = FAILED.format(day=day, step=step, reason=reason)
        return 1, [message, self.alerts.send(message)]

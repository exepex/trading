"""Issuing a built card (story T1): post it, check the host clock against Slack's and GitHub's server times, save the
full card record to Drive, then write the non-sensitive delivery metadata for the repository. Each step's failure is a
printed line and a stored fact, never a stop: the card is posted first, so a Drive outage cannot hold it back."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime

from ..server_clock import ServerClock, SkewCheck, check_server, skew_check, unchecked, utc_text
from .card import TradeCard
from .deliveries import DeliveryLog
from .posting import CardPoster, PostReceipt
from .record_store import CardRecordStore

RECORD_SCHEMA, DELIVERY_SCHEMA = "card_record/v1", "card_delivery/v1"
SLACK = "Slack"
TEST_BANNER = "TEST — PAPER ONLY: a one-off check of live delivery, not the day's card."
NOT_WRITTEN = "delivery metadata NOT written ({error}); commit it by hand:\n{metadata}"
WRITTEN = "delivery metadata written: {path} (commit and push it: its push receipt is the second issuance witness)"


@dataclass(frozen=True)
class IssueResult:
    lines: tuple[str, ...]  # what to print
    sent: bool
    saved: bool


def card_sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


class CardIssuer:
    def __init__(
        self, poster: CardPoster, records: CardRecordStore, deliveries: DeliveryLog, clocks: Sequence[ServerClock],
        host_now: Callable[[], datetime], code_commit: str,
    ):  # fmt: skip
        self.poster, self.records, self.deliveries = poster, records, deliveries
        self.clocks, self.host_now, self.code_commit = tuple(clocks), host_now, code_commit

    def issue(self, card: TradeCard, text: str, test: bool = False) -> IssueResult:
        """`test`: the one live delivery check (T1 criterion 16): marked on its first line and in both records, and
        never counted as the session's card."""
        text = f"{TEST_BANNER}\n{text}" if test else text
        before = self.host_now()
        receipt = self.poster.post(text)
        after = self.host_now()
        checks = [self._slack_check(receipt, before, after), *(check_server(c, self.host_now) for c in self.clocks)]
        facts = {**self._facts(card, text, receipt, before, after, checks), "test": test}
        record = {**facts, "schema": RECORD_SCHEMA, "text": text, "sections": [_section(s) for s in card.sections],
                  "warning": _warning(card)}  # fmt: skip
        saved, drive_line = self.records.save(
            card.day, _record_name(card, receipt, after) + ("_test" if test else ""), _json(record)
        )
        delivery = {**facts, "schema": DELIVERY_SCHEMA, "drive": {"saved": saved, "outcome": drive_line}}
        written, delivery_line = self._write(card, delivery)
        lines = (receipt.outcome, *(c.line for c in checks), drive_line, delivery_line)
        return IssueResult(lines, receipt.sent, saved and written)

    def _write(self, card: TradeCard, delivery: dict) -> tuple[bool, str]:
        try:
            return True, WRITTEN.format(path=self.deliveries.write(card.day, delivery))
        except OSError as error:  # the post is out: print the metadata so it can still be committed by hand
            return False, NOT_WRITTEN.format(error=type(error).__name__, metadata=_json(delivery).decode("utf-8"))

    @staticmethod
    def _slack_check(receipt: PostReceipt, before: datetime, after: datetime) -> SkewCheck:
        if receipt.server_time is None:
            return unchecked(SLACK, "not posted")
        return skew_check(SLACK, receipt.server_time, before, after)

    def _facts(self, card, text, receipt: PostReceipt, before, after, checks: list[SkewCheck]) -> dict:
        """What both the Drive record and the delivery metadata hold (no card text: that goes to Drive only)."""
        slack_time = receipt.server_time
        return {
            "day": card.day.isoformat(), "status": str(card.status), "reason_code": card.reason_code,
            "card_sha256": card_sha256(text), "code_commit": self.code_commit,
            "records_used": [{"path": r.path, "sha256": r.sha256} for r in card.used],
            "missing": list(card.missing), "previous_misses": list(card.previous_misses),
            "slack": {
                "sent": receipt.sent, "ts": receipt.ts, "channel": receipt.channel, "outcome": receipt.outcome,
                "server_time_utc": utc_text(slack_time) if slack_time else None,
            },
            "host_clock": {"before_utc": utc_text(before), "after_utc": utc_text(after)},
            "clock": [c.stored() for c in checks],
        }  # fmt: skip


def _section(section) -> dict:
    return {"title": section.title, "lines": list(section.lines), "missing": list(section.missing)}


def _warning(card: TradeCard) -> dict | None:
    """Story T1e: the warning kept as data in the Drive record (never in the repository's delivery metadata)."""
    return {"headline": card.warning.headline, "detail": card.warning.detail} if card.warning else None


def _record_name(card: TradeCard, receipt: PostReceipt, after: datetime) -> str:
    """Slack's ts names a sent card; an unsent one is named by the host's UTC time (each attempt its own file)."""
    stamp = receipt.ts.replace(".", "") if receipt.ts else f"unsent-{after.astimezone(UTC):%H%M%S%f}"
    return f"{card.day.isoformat()}_{stamp}"


def _json(document: dict) -> bytes:
    return (json.dumps(document, indent=1, sort_keys=True) + "\n").encode("utf-8")

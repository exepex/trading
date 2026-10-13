"""A book's submission as the repository and GitHub hold it (stories F1 and G5): its commitment and reveal, each read
at the commit that first added it (a later rewrite changes nothing), with GitHub's push time of that commit."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime

from .history import RepoHistory
from .paths import commitment_path, reveal_path
from .receipts import PushReceipts, ReceiptUnknown
from .seal import Commitment, SealBroken


@dataclass(frozen=True)
class Published:
    """One file as first published: its text, commit and GitHub receipt time (None when unknown)."""

    text: str
    commit: str
    received_at: datetime | None
    receipt_problem: str = ""


@dataclass(frozen=True)
class Submission:
    commitment: Published | None
    reveal: Published | None
    notes: list[str] = field(default_factory=list)

    def sealed(self) -> Commitment | None:
        if self.commitment is None:
            return None
        try:
            return Commitment.from_text(self.commitment.text)
        except SealBroken:
            return None


def read_submission(history: RepoHistory, receipts: PushReceipts, day: date, book: str) -> Submission:
    commitment = _published(history, receipts, commitment_path(day, book))
    reveal = _published(history, receipts, reveal_path(day, book))
    notes = [f"{p} was changed after it was first published; the first version counts"
             for p, f in ((commitment_path(day, book), commitment), (reveal_path(day, book), reveal))
             if f is not None and history.committed_text(p) != f.text]  # fmt: skip
    return Submission(commitment, reveal, notes)


def _published(history: RepoHistory, receipts: PushReceipts, path: str) -> Published | None:
    commit = history.first_commit_adding(path)
    if commit is None:
        return None
    text = history.committed_text(path, commit) or ""
    try:
        return Published(text, commit, receipts.received_at(commit))
    except ReceiptUnknown as unknown:
        return Published(text, commit, None, str(unknown))

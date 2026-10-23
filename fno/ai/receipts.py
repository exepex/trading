"""When a book's file reached the repository, by GitHub's clock (story F1's receipt time). `PushReceipts` is the
interface; `GitHubActivityReceipts` reads the repository's activity log (`ActivityLog`), where GitHub records each push
to `main` with its server timestamp and the commits before and after it. A commit's receipt is the push whose `after`
contains it and whose `before` does not. A commit's own date is set by whoever made it and is never the receipt; it
only says how far back to search (story receipts-reach), so a date set later than the real push finds no push and
fails closed. Anything unclear raises `ReceiptUnknown`, which the collector treats as late (fails closed)."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable
from datetime import datetime, timedelta

from .activity_log import ActivityLog, ReceiptAccessDenied, ReceiptUnavailable, ReceiptUnknown
from .history import RepoHistory

__all__ = ["GitHubActivityReceipts", "PushReceipts", "ReceiptAccessDenied", "ReceiptNotFound", "ReceiptOutsideLog",
           "ReceiptUnavailable", "ReceiptUnknown"]  # fmt: skip
NO_COMMIT = "0" * 40
CLOCK_MARGIN = timedelta(days=1)  # a committer's clock ahead of GitHub's still finds its push
NOT_FOUND = "no push of {commit} in GitHub's activity log of main since {since} ({pages} pages read)"
OUTSIDE = "GitHub's activity log ends at {oldest}, before {commit} could be pushed (from {since}; {pages} pages read)"


class ReceiptNotFound(ReceiptUnknown):
    """The log covers every moment the commit could have been pushed, and holds no push of it: a real answer."""


class ReceiptOutsideLog(ReceiptUnknown):
    """The log no longer reaches back to when the commit could have been pushed: the push time cannot be known."""


class PushReceipts(ABC):
    @abstractmethod
    def received_at(self, commit: str) -> datetime:
        """GitHub's time of the push that first brought `commit` to `main`, or ReceiptUnknown."""


class GitHubActivityReceipts(PushReceipts):
    def __init__(self, repository: str, token: str, history: RepoHistory, get: Callable | None = None):
        self._history, self._log = history, ActivityLog(repository, token, get)

    @property
    def pages(self) -> int:
        """Pages of the log read so far by this reader (each question reads only the pages it still needs)."""
        return self._log.pages

    def received_at(self, commit: str) -> datetime:
        since = self._history.committed_at(commit) - CLOCK_MARGIN
        for push in self._log.since(since):
            before, after = push.get("before") or NO_COMMIT, push.get("after") or ""
            new = before == NO_COMMIT or not self._history.is_ancestor(commit, before)
            if self._history.is_ancestor(commit, after) and new:
                return datetime.fromisoformat(push["timestamp"])
        fields = {"commit": commit[:10], "since": since.isoformat(), "pages": self._log.pages}
        if self._log.ended and self._log.oldest is not None and self._log.oldest > since:
            raise ReceiptOutsideLog(OUTSIDE.format(oldest=self._log.oldest.isoformat(), **fields))
        raise ReceiptNotFound(NOT_FOUND.format(**fields))

"""One pass over the circular feeds (story A20b): every circular not seen before becomes a row with the time we first
saw it; the file of each F&O-relevant one is saved first, so a row whose file failed is not written and the next run
tries again. New rows of the run form one part of the `circulars/list` table in Drive (O9)."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from datetime import UTC, date, datetime, timedelta

from ..storage.data_store import DataStore
from ..storage.part_table import PartTable
from .feeds import CircularFeed
from .model import COLUMNS, YES, Circular, FeedFailed

LIST_TABLE, FILES_FOLDER = "circulars/list", "circulars/files"
LOOKBACK = timedelta(days=1)  # each NSE run asks yesterday and today, so a missed run loses only timing precision
FEED_LINE = "{source}: {listed} listed, {new} new, {files} file(s) saved"
FEED_FAILED = "{source}: list NOT read: {error}"
FILE_FAILED = "{source} {number}: file NOT saved, the circular is left for the next run: {error}"
MAY_HAVE_SKIPPED = (
    "{source}: none of the {listed} circulars on its latest page was seen before: some may have been missed "
    "between runs (check the publisher's full list)"
)


def file_path(circular: Circular) -> str:
    return f"{FILES_FOLDER}/{circular.source}/{circular.issued_on:%Y/%m}/{circular.filename}"


class CircularCapture:
    def __init__(self, feeds: Mapping[str, CircularFeed], relevant: Callable[[Circular], bool], store: DataStore,
                 clock: Callable[[], datetime] = lambda: datetime.now(UTC), out=print):  # fmt: skip
        self.feeds, self.relevant, self.store, self.clock, self.out = feeds, relevant, store, clock, out
        self.table = PartTable(store, LIST_TABLE, COLUMNS)

    def run(self, today: date, seen: Mapping[str, str]) -> list[str]:
        """Captures every feed; returns the problems (a failed feed or file, a possible gap). `seen`: link -> source
        of every circular already listed."""
        problems, rows = [], []
        for source, feed in self.feeds.items():
            try:
                listed = feed.fetch(today - LOOKBACK, today)  # one circular per link (the feed merges NSE's repeats)
            except FeedFailed as exc:
                problems.append(FEED_FAILED.format(source=source, error=exc))
                continue
            first_seen_at = self.clock().astimezone(UTC).isoformat()
            if feed.LATEST_PAGE_ONLY and source in seen.values() and not any(c.link in seen for c in listed):
                problems.append(MAY_HAVE_SKIPPED.format(source=source, listed=len(listed)))
            new = [c for c in listed if c.link not in seen]
            kept = [row for c in new if (row := self._keep(feed, c, first_seen_at, problems))]
            rows += kept
            files = sum(row["fno_relevant"] == YES for row in kept)
            self.out(FEED_LINE.format(source=source, listed=len(listed), new=len(kept), files=files))
        if rows:
            self.table.write(today, rows)
        return problems

    def _keep(self, feed: CircularFeed, circular: Circular, first_seen_at: str, problems: list[str]) -> dict | None:
        relevant = self.relevant(circular)
        if relevant:
            try:
                self.store.put(file_path(circular), feed.download(circular))
            except (FeedFailed, RuntimeError, ValueError) as exc:  # unreachable, refused, Drive, a changed file
                problems.append(FILE_FAILED.format(source=circular.source, number=circular.number, error=exc))
                return None
        return circular.row(relevant, first_seen_at)

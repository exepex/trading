"""Story O1, gap F1 (judge 412 add. 2-3, judge 417): a 3 pm part that an earlier run started. Its output and exit code
went with that run, so it ends when its lock frees and its outcome is read from its canonical markers: `ok` "recorded
earlier (commit <sha>)" when every marker exists, otherwise `failed`. The run cannot stop it, as it did not start it."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from datetime import date

from ..quotes.recorder import QuoteSnapshotRecorder
from .processes import Process

QUOTES = "research/data/quotes/"  # the quote store's folder in the checkout (`fno/storage/wiring.py` QUOTES_FOLDER)
NOT_YET_COMMITTED = "not yet committed"
RECORDED_EARLIER = "recorded earlier (commit {commit})"
NO_RECORD = "an earlier run's recorder ended without every canonical marker: {missing}"


class PartMarkers:
    """A part's canonical markers in the checkout, and the commit that holds them."""

    def __init__(self, root, git):
        self.root, self.git = root, git

    def paths(self, day: date, canonicals: Sequence[tuple[str, str]]) -> list[str]:
        return [QUOTES + QuoteSnapshotRecorder.path(day, f"{stem}_{day:%Y%m%d}.canonical", dataset)
                for dataset, stem in canonicals]  # fmt: skip

    def missing(self, day: date, canonicals: Sequence[tuple[str, str]]) -> list[str]:
        return [path for path in self.paths(day, canonicals) if not (self.root / path).is_file()]

    def recorded(self, day: date, canonicals: Sequence[tuple[str, str]]) -> str | None:
        """The commit holding every marker, `NOT_YET_COMMITTED` when one is still to commit; None if one is missing."""
        if self.missing(day, canonicals):
            return None
        paths = self.paths(day, canonicals)
        if self.git.changed(paths):
            return NOT_YET_COMMITTED
        return self.git("log", "-1", "--format=%h", "--", *paths).stdout.strip() or NOT_YET_COMMITTED


class EarlierRun(Process):
    def __init__(self, held: Callable[[], bool], recorded: Callable[[], str | None], missing: Callable[[], list]):
        self.held, self.recorded, self.missing = held, recorded, missing
        self.code: int | None = None
        self.line = ""

    def poll(self) -> int | None:
        if self.code is None and not self.held():
            commit = self.recorded()
            self.code = 0 if commit else 1
            self.line = RECORDED_EARLIER.format(commit=commit) if commit else NO_RECORD.format(
                missing=", ".join(self.missing()))  # fmt: skip
        return self.code

    def lines(self) -> list[str]:
        return [self.line] if self.line else []

    def alerted(self) -> bool:
        return False  # whatever its recorder alerted went with the earlier run: O1 alerts a failure once

    def stop(self) -> None:
        """Never stopped here: the alert gives the hand fix (stop it, then rerun)."""

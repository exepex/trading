"""The session's public counts (story 3.4, privacy), written and committed by the fleet's single runner (MS-P1c's
assumption: one writer per session): c's outcome counts per road and driver, and the three counts (MS-P1f) per road,
driver and session, codes and whole numbers only. Both files are write-once: the same text again is a no-op."""

import csv
import io
from collections.abc import Iterable
from datetime import date
from pathlib import Path
from typing import Protocol

from ..contracts.dashcam import ReplayConflict
from ..contracts.records import DecisionRecord
from ..contracts.tickets import OpportunityCounts
from ..dashcam.counts import PublicCountsFile
from ..dashcam.names import counts_path

OPPORTUNITY_HEADER = ("session", "road", "driver", "eligible", "fillable", "executed")
OPPORTUNITY_SUFFIX = ".opportunity.csv"
COMMIT_WHAT = "school counts {session}"


class CountsCommitter(Protocol):
    def commit(self, what: str) -> str: ...


def opportunity_path(session: date, slot: str) -> Path:
    plain = Path(counts_path(session, slot))
    return plain.with_name(plain.stem + OPPORTUNITY_SUFFIX)


def opportunity_text(counts: Iterable[OpportunityCounts]) -> str:
    out = io.StringIO()
    writer = csv.writer(out, lineterminator="\n")
    writer.writerow(OPPORTUNITY_HEADER)
    rows = sorted(
        (c.session.isoformat(), c.road.value, c.driver_id, c.eligible, c.fillable, c.executed) for c in counts
    )
    writer.writerows(rows)
    return out.getvalue()


class SessionCounts:
    def __init__(self, root: Path, committer: CountsCommitter | None):
        """`committer` None writes only (tests, replays); the daily run commits and pushes."""
        self.root, self.committer = Path(root), committer
        self.outcomes = PublicCountsFile(self.root)

    def write(self, session: date, slot: str, records: tuple[DecisionRecord, ...],
              counts: tuple[OpportunityCounts, ...]) -> str:  # fmt: skip
        self.outcomes.write(session, slot, records)
        file, text = self.root / opportunity_path(session, slot), opportunity_text(counts)
        if file.is_file() and file.read_text() != text:
            raise ReplayConflict(f"rule broken: {opportunity_path(session, slot)} holds other counts")
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_text(text)
        return self.committer.commit(COMMIT_WHAT.format(session=session)) if self.committer else ""

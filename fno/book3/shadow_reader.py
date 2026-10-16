"""Book 3's shadow decisions as scoreboard A reads them (story F7): per common opportunity `take` (with D4's
`BookTerms` at one lot), `skip`, or `not observed` (S3's `matched_actions` kinds). Only a file committed before the
day's execution snapshot counts (D3's on-time rule); a late, missing or edited file, or one written for another common
pack, reads as `not observed` for every opportunity of the day. S3's reading of it is S3's builder's (slice E)."""

from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Protocol

from ..desk.common_pack import CommonPack
from ..desk.opportunity_set import NO_TRADE_OPPORTUNITY
from ..playbook.decision_timing import LATE, CommitTimes, file_timeliness
from ..playbook.envelope import BookTerms
from ..scoreboard.matched_actions import NOT_OBSERVED, SKIP, TAKE
from .shadow_file import NO_DECISION, NO_TRADE, shadow_path

STANDARD_LOTS = 1  # scoreboard A's unit (S1 `scoreboard_a_standardisation`)
NO_FILE, NO_SNAPSHOT = "no decision (no shadow file)", "no execution snapshot time for the day"
EDITED, OTHER_PACK = "shadow file is not as written (edited)", "shadow file names another common pack"


class ShadowGit(CommitTimes, Protocol):
    def added_in(self, path: str) -> tuple[str, str] | None: ...

    def committed_bytes(self, path: str, commit: str) -> bytes | None: ...


@dataclass(frozen=True)
class ShadowAction:
    kind: str  # TAKE, SKIP or NOT_OBSERVED
    reason: str
    terms: BookTerms | None = None


class Book3ShadowReader:
    def __init__(self, root: Path, git: ShadowGit, common: Callable[[date], CommonPack | None],
                 snapshot_started_at: Callable[[date], datetime | None]):  # fmt: skip
        self.root, self.git, self.common, self.started = Path(root), git, common, snapshot_started_at

    def actions(self, day: date) -> dict[str, ShadowAction]:
        pack = self.common(day)
        if pack is None:
            return {}
        ids = [o["opportunity_id"] for o in pack.body["opportunities"] if o != NO_TRADE_OPPORTUNITY]
        body, problem = self._body(day, pack)
        if problem:
            return {i: ShadowAction(NOT_OBSERVED, problem) for i in ids}
        entries = {e["opportunity_id"]: e for e in body["entries"]}
        return {i: _action(entries.get(i)) for i in ids}

    def _body(self, day: date, pack: CommonPack) -> tuple[dict | None, str]:
        path = self.root / shadow_path(day)
        if not path.is_file():
            return None, NO_FILE
        started = self.started(day)
        if started is None:
            return None, NO_SNAPSHOT
        status, why = file_timeliness(shadow_path(day), started, self.git)
        if status == LATE:
            return None, f"late: {why}"
        data, added = path.read_bytes(), self.git.added_in(shadow_path(day))
        if added is None or self.git.committed_bytes(shadow_path(day), added[0]) != data:
            return None, EDITED  # read only as the commit that added it wrote it
        body = json.loads(data)
        if body["common_pack_sha256"] != pack.sha256:
            return None, OTHER_PACK
        return body, ""


def _action(entry: dict | None) -> ShadowAction:
    if entry is None or entry["action"] == NO_DECISION:
        return ShadowAction(NOT_OBSERVED, entry["reason"] if entry else "no entry")
    if entry["action"] == NO_TRADE:
        return ShadowAction(SKIP, entry["reason"])
    terms = BookTerms((entry["strategy"], int(entry["version"])), float(entry["width"]), STANDARD_LOTS)
    return ShadowAction(TAKE, entry["reason"], terms)

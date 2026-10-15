"""Scoreboard A, matched decisions (story S3): every book's actions on the same common opportunities, valued as one
standard unit, per book (pilot apart, head-to-head per D6 segment) and per pair of books, with S1's uncertainty
criterion, Holm across the head-to-head claims and the miss cap. Output: `research/scoreboards/A/<date>.json`,
canonical JSON kept in Drive (story E2c: one-lot fills at the touch are per-contract data). Never merged with B."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from datetime import date
from itertools import permutations
from pathlib import Path

from .book_trades import Sessions
from .entry_decisions import EntryDecisions
from .matched import counts as section_counts
from .matched import judged, pair_series, scored_days, series_of, value_takes
from .matched_days import F7_NOT_BUILT, MISSES, NO_PACK, NO_SNAPSHOT, UNSCORED, BookDay, CommonSet, MatchedDays
from .standard_unit import StandardUnit
from .uncertainty import holm
from .whole_system import canonical

KIND, OUTPUT_FOLDER = "scoreboard_a", "research/scoreboards/A"
MISS_CAP = 0.10  # share of a book's eligible sessions (G9's figure, owner row 170; frozen by S1's `missed_runs`)
UNDECIDED_OPERATIONS, UNDECIDED_F7, NOT_STARTED, CLAIM, NO_CLAIM = (
    "undecided, operations", "undecided, F7 not built", "not started", "claim allowed", "no claim",
)  # fmt: skip
APART = frozenset({NO_SNAPSHOT, NO_PACK, UNSCORED, F7_NOT_BUILT})


class MatchedBoard:
    def __init__(self, books: Sequence[str], days: Callable[[EntryDecisions], MatchedDays],
                 decisions: Callable[[], EntryDecisions], packs: Callable[[date], CommonSet | None],
                 sessions: Sessions, unit: StandardUnit, first_day: Callable[[], date | None],
                 protocol_label: str):  # fmt: skip
        self.books, self.days, self.decisions, self.packs = tuple(books), days, decisions, packs
        self.sessions, self.unit, self.first_day, self.protocol_label = sessions, unit, first_day, protocol_label

    def build(self, on: date) -> dict:
        decisions, first = self.decisions(), self.first_day()
        sessions = list(self.sessions(first, on)) if first and first <= on else []
        matched = self.days(decisions)
        book_days = {book: [matched.book_day(book, day) for day in sessions] for book in self.books}
        entries = {(day, e["opportunity_id"]): e for day in sessions for e in self._entries(day)}
        results = value_takes((d for days in book_days.values() for d in days), entries, self.unit, on)
        start = decisions.common_start(self.books)
        board = {
            "kind": KIND, "date": on.isoformat(), "protocol": self.protocol_label, "miss_cap": MISS_CAP,
            "common_start": start.isoformat() if start else None,
            "books": {b: self._book(days, results, start) for b, days in book_days.items()},
            "pairs": self._pairs(book_days, results, start),
            "actions": _rows(book_days, results),
        }  # fmt: skip
        _apply_holm(board)
        return board

    def _entries(self, day: date) -> tuple:
        common = self.packs(day)
        return common.opportunities if common else ()

    def _book(self, days: list[BookDay], results, start: date | None) -> dict:
        pilot = [d for d in days if start is None or d.day < start]
        later = [d for d in days if start is not None and d.day >= start]
        head = self._section(later, results) if start else None
        if head is not None:
            labels = sorted({d.segment for d in later if d.observed})
            head["segments"] = {s: self._section([d for d in later if d.segment == s], results) for s in labels}
        return {"verdict": "", **_misses(days), "pilot": self._section(pilot, results), "head_to_head": head}

    @staticmethod
    def _section(days: list[BookDay], results) -> dict:
        scores = scored_days(days, results)
        return {**section_counts(days, results), "judged": judged(series_of(scores), sum(s.closed for s in scores))}

    def _pairs(self, book_days: dict[str, list[BookDay]], results, start: date | None) -> dict:
        if start is None:
            return {}
        pairs = {}
        for first, second in permutations(self.books, 2):  # "X beats Y" and "Y beats X" are separate claims
            a = scored_days([d for d in book_days[first] if d.day >= start], results)
            b = scored_days([d for d in book_days[second] if d.day >= start], results)
            series = pair_series(a, b)
            shared = set(series.days)
            positions = sum(s.closed for s in (*a, *b) if s.day in shared)  # both books' positions on shared days
            pairs[f"{first} - {second}"] = {
                "judged": judged(series, positions) if series.days else {"days": 0, "reason": "no common day"},
                "daily_rs": [[d.isoformat(), round(n, 2)] for d, n in zip(series.days, series.net, strict=True)],
                "not_observed_days": {first: _unobserved(book_days[first], start),
                                      second: _unobserved(book_days[second], start)},
            }  # fmt: skip
        return pairs


def _unobserved(days: list[BookDay], start: date) -> int:
    return sum(not d.observed for d in days if d.day >= start)


def _misses(days: list[BookDay]) -> dict:
    """The miss cap counts from the book's first collected run ("not started" before it); days without a snapshot or a
    common pack, D6-unscored days and Book 3's days before F7 are counted apart, outside the cap (design 6)."""
    started = [i for i, d in enumerate(days) if d.observed or d.observed_reason == UNSCORED]
    since = days[started[0] :] if started else []
    eligible = [d for d in since if d.observed_reason not in APART]
    misses = sum(d.observed_reason in MISSES for d in eligible)
    share = misses / len(eligible) if eligible else None
    f7 = any(d.observed_reason == F7_NOT_BUILT for d in days)
    return {"eligible_days": len(eligible), "misses": misses, "f7_not_built": f7, "started": bool(started),
            "miss_share": None if share is None else round(share, 6)}  # fmt: skip


def _rows(book_days: dict[str, list[BookDay]], results) -> list[dict]:
    rows = []
    for days in book_days.values():
        for d in days:
            for opportunity_id, action in sorted(d.actions.items()):
                result = results.get((d.book, d.day, opportunity_id))
                rows.append({
                    "book": d.book, "day": d.day.isoformat(), "opportunity_id": opportunity_id, "action": action.kind,
                    "reason": action.reason, "status": result.status if result else None,
                    "net_rs": result.net if result else None, "max_loss_rs": result.max_loss if result else None,
                    "exited_on": result.exited_on.isoformat() if result and result.exited_on else None,
                })  # fmt: skip
    return rows


def _apply_holm(board: dict) -> None:
    """Holm across the head-to-head claims whose sample is met (S1); then each book's verdict."""
    claims = [entry["head_to_head"]["judged"] for entry in board["books"].values() if entry["head_to_head"]]
    claims += [pair["judged"] for pair in board["pairs"].values() if pair["judged"].get("days")]
    tested = [c for c in claims if c.get("sample_met") and c.get("p_value") is not None]
    for claim, passed in zip(tested, holm([c["p_value"] for c in tested]), strict=True):
        claim["holm_pass"] = passed
    for entry in board["books"].values():
        entry["verdict"] = _verdict(entry)


def _verdict(entry: dict) -> str:
    if entry["f7_not_built"]:
        return UNDECIDED_F7
    if not entry["started"]:
        return NOT_STARTED
    if entry["miss_share"] is not None and entry["miss_share"] > MISS_CAP:
        return UNDECIDED_OPERATIONS
    head = entry["head_to_head"]
    if head and head["judged"].get("claim_allowed") and head["judged"].get("holm_pass"):
        return CLAIM
    return NO_CLAIM


def write_board(root: Path, board: dict) -> Path:
    path = Path(root) / OUTPUT_FOLDER / f"{board['date']}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(canonical(board), encoding="utf-8")
    return path

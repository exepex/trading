"""One stress-factor run (story A14c): coverage first, then each family's largest needed factor, then one row per
structure family (debit, credit; owner, 16 Oct 2026) in the factor file.

Full or incremental. The rule is a maximum over a window that only grows, so an incremental run reads the sessions
from `LOOKBACK_DAYS` before the earlier of the families' `coverage_through` (longer than any holding) and counts, per
family, only the holdings that end after that family's own date, taking the larger of their needed factor
(`held_rise`) and the family's last `unrounded`. The run is full when any family has no measured row of its own (the
owner's seed and the rows before the family column), so a hand value never becomes a floor (judge 176). Every file
must be the archive's first copy (its SHA-256 equals the manifest's) and written before 09:00 IST on its day (A14's
point-in-time rule). Files are read ahead by `workers` threads but fed in day order. Any refusal (a download error
included) writes nothing and sends one #fno-desk line; so does every run that writes its rows."""

from __future__ import annotations

import hashlib
import re
import traceback
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path

from ..alerts.sender import AlertSender
from ..constants import SPAN_BOD_CREATED_BEFORE, STRESS_FAMILIES
from ..fo_bhavcopy import BadFile
from .family_result import FamilyResult, family_result
from .held_rise import HeldRises, HeldRiseTracker
from .job import DayFile
from .prefetch import in_order
from .span_file import SpanFile, read_span_file
from .stress_coverage import FIRST_SESSION, CoverageGap, check_coverage, required_sessions
from .stress_evidence import build_evidence
from .stress_log import NextRow, StressFactorFile, StressRowRefused

COMMIT_SHA = re.compile(r"[0-9a-f]{7,40}")  # the owner's DESK_DECISIONS commit approving a fall
LOOKBACK_DAYS = 60  # a holding lasts at most about 44 calendar days (expiry 30-65 days out, exit 21 days before)
HEADLINE = "Omenix F&O stress factor {run_day}: "
WRITTEN = "{family} {status} {factor:g} (computed {computed:g}, was {was:g}), peak {peak}"
HELD_ASK = "; a lower value waits for the owner: approve it with a DESK_DECISIONS row, then rerun with --approve-fall"
DROPPED = "; {count} holding(s) dropped, not entered or skipped for an impossible price (named in the evidence)"
REFUSED = "Omenix F&O stress factor {run_day}: nothing written: {reason}"


@dataclass(frozen=True)
class StressSources:
    day_file: DayFile  # a session's first-archived i1 file; called from `workers` threads at once
    archived: Callable[[], Mapping[date, str]]  # the manifest: session -> SHA-256
    is_trading_day: Callable[[date], bool]
    new_tracker: Callable[[], HeldRiseTracker]
    first_session: date = FIRST_SESSION
    workers: int = 1  # downloads running ahead of the day being read (prefetch.in_order)


class StressFactorRun:
    def __init__(self, sources: StressSources, factor_file: StressFactorFile, evidence_folder: Path,
                 alerts: AlertSender, run_day: date, print_line=print):  # fmt: skip
        self.sources, self.factor_file, self.evidence_folder = sources, factor_file, evidence_folder
        self.alerts, self.run_day, self.print_line = alerts, run_day, print_line

    def run(self, full: bool = False, approved_fall: str | None = None) -> int:
        try:
            line = self._run(full, approved_fall)
        except (CoverageGap, StressRowRefused, BadFile) as exc:
            return self._refused(exc)
        except Exception as exc:  # e.g. Drive consent expired, a calendar year missing: still one line, never silent
            traceback.print_exc()
            return self._refused(f"stopped by an unexpected {type(exc).__name__}: {exc}")
        self.print_line(self.alerts.send(line))
        return 0

    def _refused(self, reason) -> int:
        self.print_line(self.alerts.send(REFUSED.format(run_day=self.run_day, reason=reason)))
        return 1

    def _run(self, full: bool, approved_fall: str | None) -> str:
        if approved_fall is not None and not COMMIT_SHA.fullmatch(approved_fall):
            raise StressRowRefused(f"--approve-fall must be a commit SHA (7-40 hex characters), not {approved_fall!r}")
        required = required_sessions(self.run_day, self.sources.is_trading_day, self.sources.first_session)
        coverage = check_coverage(required, self.sources.archived())
        lasts = {family: self.factor_file.last(family) for family in STRESS_FAMILIES}
        full = full or any(last.unrounded is None or last.coverage_through is None for last in lasts.values())
        through = None if full else min(last.coverage_through for last in lasts.values())
        start = self.sources.first_session if full else through - timedelta(days=LOOKBACK_DAYS)
        tracker = self._read([d for d in required if d >= start], coverage.files)
        results = [family_result(family, tracker.found.completed, lasts[family], full, approved_fall)
                   for family in STRESS_FAMILIES]  # fmt: skip
        evidence = build_evidence(
            self.run_day, results, coverage.files, tracker.found, "full" if full else "incremental"
        )
        evidence.write(self.evidence_folder, self.run_day)
        self.factor_file.append([NextRow(self.run_day, r.factor, r.computed, r.unrounded, r.status, r.peak,
                                         coverage.through, evidence.sha256, r.family) for r in results])  # fmt: skip
        return _line(self.run_day, results, tracker.found)

    def _read(self, days: list[date], sha256: Mapping[date, str]) -> HeldRiseTracker:
        tracker = self.sources.new_tracker()
        try:
            for day, (filename, data) in in_order(self.sources.day_file, days, self.sources.workers):
                tracker.feed(day, self._span(filename, data, day, sha256[day]))
        except OSError as exc:  # Drive unreachable or refusing (requests' errors are OSErrors): nothing is written
            raise StressRowRefused(f"the archive could not be read: {exc}") from exc
        return tracker

    def _span(self, filename: str, data: bytes | None, day: date, sha256: str) -> SpanFile:
        if data is None:
            raise StressRowRefused(f"{filename} is in the manifest but not in the archive")
        if hashlib.sha256(data).hexdigest() != sha256:
            raise StressRowRefused(f"{filename} differs from its manifest SHA-256 (not the first-archived copy)")
        span = read_span_file(data, filename, allow_short_option_minimum=True)
        deadline = datetime.combine(day, SPAN_BOD_CREATED_BEFORE, tzinfo=span.created.tzinfo)
        if span.created >= deadline:
            raise StressRowRefused(f"{filename} was written {span.created:%Y-%m-%d %H:%M}, not before 09:00 on its day")
        return span


def _line(run_day: date, results: list[FamilyResult], found: HeldRises) -> str:
    families = "; ".join(WRITTEN.format(family=r.family, status=r.status, factor=r.factor, computed=r.computed,
                                        was=r.last.factor, peak=r.peak) for r in results)  # fmt: skip
    skipped = len(found.dropped) + len(found.impossible)
    held = any(r.status == "held" for r in results)
    return (
        HEADLINE.format(run_day=run_day)
        + families
        + (DROPPED.format(count=skipped) if skipped else "")
        + (HELD_ASK if held else "")
    )

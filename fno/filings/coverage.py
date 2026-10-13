"""Coverage of the filings archive (story A12), read-only: per filing type, how many companies of the list have files,
how many files the manifest lists, and whether the archive holds each one unchanged (Drive's MD5 against the
manifest's, from one folder listing per company). A file in the archive without a manifest row is unfingerprinted;
a listed file missing or with another MD5 is damaged. Every gap is printed with its reason.

The half-year check (criterion 6): for each recent half-year end (September, March) whose filing deadline has passed,
the share of companies whose results for it hold both a balance sheet and a cash-flow statement.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import date, timedelta

from ..constants import FILING_FILE_KINDS, FILING_RESULTS, FILING_SHAREHOLDING
from ..storage.raw_store import RawFileStore
from .filing import FilingGap, company_folder
from .manifest import ArchivedFiling, FilingManifest

HALF_YEAR_ENDS = ((9, 30), (3, 31))
RESULTS_DEADLINE = {3: timedelta(days=60)}  # SEBI LODR 33: 45 days after a quarter, 60 after the year's end
QUARTER = timedelta(days=45)
HALF_YEARS_CHECKED = 6
HALF_YEAR_TARGET = 0.90
FIRST_PERIOD = date(2023, 9, 30)  # the first quarter the 3-year archive covers in full
SHAREHOLDING_DEADLINE = timedelta(days=21)  # SEBI LODR 31: within 21 days of the quarter's end
NO_PERIOD = "NSE's lists hold no {kind} filing for the quarter ended {end} (not listed then, or not filed)"
NO_RESULTS_FILE, NO_STATEMENTS = "no results file", "results file without a readable balance sheet and cash flow"


@dataclass
class KindCoverage:
    kind: str
    companies: int
    covered: int = 0
    files: int = 0
    present: int = 0
    damaged: list[str] = field(default_factory=list)
    unfingerprinted: list[str] = field(default_factory=list)
    gaps: list[FilingGap] = field(default_factory=list)
    missing_periods: list[str] = field(default_factory=list)  # "SYMBOL: reason", explained, not damage
    outside_layout: list[str] = field(default_factory=list)  # files directly in a company folder (trial, 13 Oct 2026)

    @property
    def ok(self) -> bool:
        return not (self.damaged or self.unfingerprinted)


class FilingsCoverage:
    def __init__(self, store: RawFileStore, manifest: FilingManifest, gaps: Sequence[FilingGap]):
        self.store, self.manifest, self.gaps = store, manifest, gaps

    def run(
        self, companies: Sequence[str], today: date, kinds: Sequence[str] = FILING_FILE_KINDS
    ) -> list[KindCoverage]:
        return [self._kind(kind, companies, today) for kind in kinds]

    def _kind(self, kind: str, companies: Sequence[str], today: date) -> KindCoverage:
        result = KindCoverage(kind, len(companies), gaps=[g for g in self.gaps if g.kind == kind])
        by_company: dict[str, list[ArchivedFiling]] = {}
        for row in self.manifest.rows(kind).values():
            by_company.setdefault(row.filing.symbol, []).append(row)
        for symbol in companies:
            rows = by_company.get(symbol, [])
            result.covered += bool(rows)
            result.files += len(rows)
            self._check_folder(kind, symbol, rows, result)
            held = {r.filing.period_end for r in rows}
            result.missing_periods += [
                f"{symbol}: {NO_PERIOD.format(kind=kind, end=end)}"
                for end in quarter_ends(today, kind)
                if end not in held
            ]
        return result

    def _check_folder(self, kind: str, symbol: str, rows: list[ArchivedFiling], result: KindCoverage) -> None:
        folder = company_folder(kind, symbol)
        result.outside_layout += [f"{symbol}/{name}" for name in self.store.checksums(folder)]
        held = {}
        for year in self.store.folders(folder):
            held.update({f"{year}/{name}": md5 for name, md5 in self.store.checksums(f"{folder}/{year}").items()})
        listed = {f"{r.filing.period_end.year}/{r.filing.filename}": r.md5 for r in rows}
        for name, md5 in listed.items():
            if held.get(name) == md5:
                result.present += 1
            else:
                result.damaged.append(f"{symbol}/{name}: " + ("missing" if name not in held else "MD5 differs"))
        result.unfingerprinted += [f"{symbol}/{name}" for name in held if name not in listed]


def quarter_ends(today: date, kind: str) -> list[date]:
    """Every quarter end from FIRST_PERIOD whose filing deadline for that type has passed, oldest first."""
    ends, end = [], FIRST_PERIOD
    while True:
        deadline = SHAREHOLDING_DEADLINE if kind == FILING_SHAREHOLDING else RESULTS_DEADLINE.get(end.month, QUARTER)
        if end + deadline >= today:
            return ends
        ends.append(end)
        end = _next_quarter_end(end)


def _next_quarter_end(end: date) -> date:
    month = end.month % 12 + 3
    year = end.year + (end.month == 12)
    return date(year, month, 30 if month in (6, 9) else 31)


def half_years(today: date, count: int = HALF_YEARS_CHECKED) -> list[date]:
    """The `count` most recent September and March ends whose results deadline has passed, newest first."""
    ends, year = [], today.year
    while len(ends) < count:
        for month, day in HALF_YEAR_ENDS:
            end = date(year, month, day)
            if end + RESULTS_DEADLINE.get(month, QUARTER) < today and len(ends) < count:
                ends.append(end)
        year -= 1
    return sorted(ends, reverse=True)


def half_year_shares(manifest: FilingManifest, companies: Sequence[str], ends: Sequence[date]) -> dict[date, float]:
    """Half-year end -> share of companies with a results file for it holding a balance sheet and a cash flow."""
    full = {
        (r.filing.symbol, r.filing.period_end)
        for r in manifest.rows(FILING_RESULTS).values()
        if r.balance_sheet and r.cash_flow
    }
    wanted = set(companies)
    return {end: sum((s, end) in full for s in wanted) / max(len(wanted), 1) for end in ends}


def half_year_misses(manifest: FilingManifest, companies: Sequence[str], end: date) -> dict[str, str]:
    """Company -> why it lacks a balance sheet and cash flow for the half-year (no file, or a file without them)."""
    rows = [r for r in manifest.rows(FILING_RESULTS).values() if r.filing.period_end == end]
    full = {r.filing.symbol for r in rows if r.balance_sheet and r.cash_flow}
    filed = {r.filing.symbol for r in rows}
    return {s: NO_STATEMENTS if s in filed else NO_RESULTS_FILE for s in companies if s not in full}

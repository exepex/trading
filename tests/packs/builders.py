"""Fixtures for story E2's pack tests: a repository folder holding the committed golden A4 snapshot of 13 Oct 2026
(G1 v2 case A), official closes, events and a playbook, and pack builders over it."""

from __future__ import annotations

import shutil
from datetime import date, time
from pathlib import Path

from fno.composition import build_session_calendar
from fno.config import ROOT
from fno.desk.common_pack import CommonPackBuilder
from fno.desk.opportunity_set import OpportunitySet
from fno.desk.reference_inputs import ClosesInput, EventsInput, SessionInput
from fno.desk.snapshot_inputs import SnapshotInput
from fno.forecast.closes_source import CommittedClosesFile
from fno.playbook.loader import Playbook
from fno.playbook.opportunities import OpportunityFinder
from fno.playbook.registry import RegistryRow
from fno.playbook.schema import parse_strategy
from fno.quotes.recorder import DATASET
from fno.research_data.events import read_events
from fno.research_engine.cycles import TradingDays
from fno.storage.raw_store import LocalFolderStore
from tests.playbook.builders import document

DAY = date(2026, 10, 13)
CUTOFF = time(15, 0)
GOLDEN_QUOTES = ROOT / "research" / "forecasts" / "v2" / "golden" / "case_a" / "quotes"
SNAPSHOT = "nifty_20261013_145600"
EVENTS_HEADER = (
    "date,type,scheduled,announced_on,announcement_source_url,revised_from,description,source_url,"
    "first_announced_on,first_announcement_source_url,first_withdrawn_on\n"
)


def snapshot_folder(root: Path) -> Path:
    """A copy of the golden snapshot that a test may change."""
    target = root / "quotes"
    shutil.copytree(GOLDEN_QUOTES, target)
    return target / DATASET / "2026" / "10"


def write_closes(root: Path, days: list[date]) -> Path:
    path = root / "closes.csv"
    rows = "".join(f"{d.isoformat()},regular,22000.0,15.0,file,sha\n" for d in days)
    path.write_text("date,session,underlying,vix,index_file,index_sha256\n" + rows, encoding="utf-8")
    return path


def event_row(day: str, announced: str, kind: str = "rbi_policy") -> str:
    url = "https://rbi.org.in/x"
    return f"{day},{kind},yes,{announced},{url},,policy meeting,{url if day < '2026-10-14' else ''},,,\n"


class FixedPlaybook:
    def __init__(self, strategies=(), rows=()):
        self.strategies, self.rows = tuple(strategies), tuple(rows)

    def load(self):
        return Playbook(self.strategies, frozenset(r.key for r in self.rows))

    def registry_rows(self):
        return self.rows


def approved(name: str, min_days: int = 30, max_days: int = 41, on: date = date(2026, 10, 1), **changes):
    doc = document(name=name, status="paper", **changes)
    doc["structure"]["expiry"] = {"kind": "monthly", "min_days": min_days, "max_days": max_days,
                                  "exit_days_before_expiry": 21}  # fmt: skip
    strategy = parse_strategy(doc)
    row = RegistryRow(name, 1, strategy.parameters_sha256, "paper", on, "owner", "abcdef1")
    return strategy, row


def opportunity_set() -> OpportunitySet:
    return OpportunitySet(OpportunityFinder(TradingDays(build_session_calendar())))


def builder(root: Path, playbook=None, events: str = "", closes_days=(date(2026, 10, 9), date(2026, 10, 12))):
    calendar = build_session_calendar()
    inputs = (
        SnapshotInput(LocalFolderStore(root / "quotes"), DATASET),
        SessionInput(calendar),
        ClosesInput(CommittedClosesFile(write_closes(root, list(closes_days)))),
        EventsInput(tuple(read_events(EVENTS_HEADER + events, today=DAY)), "events.csv"),
    )
    return CommonPackBuilder(inputs, opportunity_set(), playbook or FixedPlaybook())

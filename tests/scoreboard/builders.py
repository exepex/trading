"""Story S2 fixtures: committed D3 records and E3 run logs written as the desk writes them, a D6 registry whose git
history is a fixed order of commits, and fixed marks."""

from __future__ import annotations

import json
from datetime import date

from fno.books.version_registry import VersionRow
from fno.books.versions import Segment, Versions
from fno.constants import JOURNAL_FOLDER
from fno.desk.run_log import RUNS_FOLDER
from fno.playbook.decision_record import NO_TRADE_ID
from fno.playbook.decision_store import DecisionStore, record_file
from fno.scoreboard.entry_facts import EntryFacts

SERVED = {"playbook": "pb-1", "config": "cfg-1"}
COMMITS = ("c0", "c1", "c2", "c3", "c4", "c5", "c6", "c7", "c8", "c9")  # oldest first


def facts(max_loss=5000.0, overridden=False, label="v1") -> EntryFacts:
    segment = Segment("book1_rules", label, "matches")
    return EntryFacts("r/o", date(2026, 10, 14), max_loss, 9000.0, 0.0, 0.4, overridden, segment)


class OrderedHistory:
    """Git as a fixed line of commits; every registry row is in the first."""

    def first_commit_containing(self, text, path):
        return COMMITS[0]

    def is_ancestor(self, older, newer):
        return COMMITS.index(older) <= COMMITS.index(newer)


def versions(*rows: tuple[str, str, date], served=SERVED) -> Versions:
    registry = [VersionRow(book, version_id, start, "c0", dict(served), "fixture") for book, version_id, start in rows]
    return Versions(registry, OrderedHistory())


def record(book, day, run_id, opportunity_id, max_loss=None, served=SERVED, override=None, margin=9000.0, stress=None,
           reserve=0.0):  # fmt: skip
    """A D3 record: a chosen trade when `max_loss` is given, else the run's day record."""
    body = {"run_id": run_id, "opportunity_id": opportunity_id, "book": book, "served": dict(served),
            "owner_override": override, "header": {}, "expected": None, "risk": None}  # fmt: skip
    if max_loss is not None:
        capital = {f"x-{opportunity_id}": {"capital_tied": margin, "stress_reserve": reserve}}
        verdicts = [{"rule": "margin_room", "numbers": {"capital_rs": capital}}]
        if stress:
            verdicts.append({"rule": "stress_loss", "numbers": {"worst_loss_rs": stress[0], "limit_rs": stress[1]}})
        body |= {"expected": {"worst_rs": -max_loss}, "risk": {"trade_id": f"x-{opportunity_id}", "verdicts": verdicts}}
    return body


def write_run(root, book, day, run_id, *records):
    """A committed run: the given records and its day record, all with the run's served components (D3 sets them
    per run)."""
    folder = DecisionStore(root, book).day_folder(day) / run_id
    folder.mkdir(parents=True, exist_ok=True)
    served = records[0]["served"] if records else SERVED
    for body in (*records, record(book, day, run_id, NO_TRADE_ID, served=served)):
        (folder / record_file(body["opportunity_id"])).write_text(json.dumps(body, sort_keys=True))
    (folder / "inputs.json").write_text("{}")


def write_log(root, day, runs, commit="c5", committed="15:05:00", snapshot_started="15:15:00", snapshot_id=None):
    """E3's run log for `day`: each book's collected run (book -> run ID, or None when late) and a valid snapshot."""
    at = lambda clock: f"{day.isoformat()}T{clock}+05:30"  # noqa: E731
    decisions = {
        book: {"run_id": run_id, "commit": commit, "committed_at": at(committed)} if run_id else {"decision": "late"}
        for book, run_id in runs.items()
    }
    steps = {
        "decisions": {"started_at": at("15:12:00"), "finished_at": at("15:12:05"), "inputs": {}, "result": decisions},
        "snapshot": {"started_at": at(snapshot_started), "finished_at": at("15:15:30"), "inputs": {},
                     "result": {"valid": True, "snapshot_id": snapshot_id or f"snap-{day.isoformat()}"}},
    }  # fmt: skip
    path = root / JOURNAL_FOLDER / RUNS_FOLDER / f"{day.isoformat()}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"day": day.isoformat(), "kind": "daily_run", "steps": steps}))

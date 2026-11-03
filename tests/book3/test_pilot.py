"""Story F6 criterion 10: no pilot label is stored. Book 3's real runs sit in D3's store, so S2's common-start rule
reads them with the other books' runs: before every book has an on-time run under its registered version, every Book 3
decision is pilot evidence; the first day all three have one is the common start."""

import json
from datetime import date

from fno.books.version_registry import VersionRow
from fno.books.versions import Versions
from fno.constants import BOOK1_RULES, BOOK2_HYBRID, BOOK3_AI, BOOKS
from fno.scoreboard.committed_runs import CommittedRuns
from fno.scoreboard.entry_decisions import EntryDecisions
from fno.scoreboard.sources import RecordedOwnerOverride
from tests.book3.engine_builders import DAY, accepted, decider, decision, repository, spec
from tests.scoreboard.builders import SERVED, OrderedHistory, record, write_log, write_run


def book3_run(root):
    repository(root, [spec()])
    out = decider(root).decide(accepted(root, decision()))
    return out.run.name, json.loads((out.run / "no_trade.json").read_text())["served"]


def common_start(root, book3_served, books=BOOKS):
    rows = [VersionRow(b, f"{b}-v1", date(2026, 10, 1), "c0", dict(book3_served if b == BOOK3_AI else SERVED), "t")
            for b in books]  # fmt: skip
    found = CommittedRuns(root)
    decisions = EntryDecisions(found.runs(), found.records, Versions(rows, OrderedHistory()), RecordedOwnerOverride())
    return decisions.common_start(BOOKS)


def other_books(root, run_id):
    for book in (BOOK1_RULES, BOOK2_HYBRID):
        write_run(root, book, DAY, run_id, record(book, DAY, run_id, "x"))


def test_book3_alone_is_pilot_evidence(tmp_path):
    run_id, served = book3_run(tmp_path)
    write_log(tmp_path, DAY, {BOOK3_AI: run_id})
    assert common_start(tmp_path, served) is None


def test_the_first_day_all_three_books_are_on_time_is_the_common_start(tmp_path):
    run_id, served = book3_run(tmp_path)
    other_books(tmp_path, run_id)
    write_log(tmp_path, DAY, dict.fromkeys(BOOKS, run_id))
    assert common_start(tmp_path, served) == DAY


def test_a_late_book3_run_keeps_the_day_pilot(tmp_path):
    run_id, served = book3_run(tmp_path)
    other_books(tmp_path, run_id)
    write_log(tmp_path, DAY, dict.fromkeys(BOOKS, run_id), committed="15:16:00")
    assert common_start(tmp_path, served) is None


def test_book3_s_records_carry_no_stored_pilot_label(tmp_path):
    run_id, _ = book3_run(tmp_path)
    folder = tmp_path / "journal" / BOOK3_AI / "decisions" / DAY.isoformat() / run_id
    texts = [p.read_text() for p in folder.glob("*.json") if p.name != "inputs.json"]
    assert texts and not any('"pilot"' in t for t in texts)

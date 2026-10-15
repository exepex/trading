"""Story A17 on the committed files: every row names a logged copy, back-filled history is marked as such, the
committed checks are what the code writes, RBI and FBIL agree wherever both publish, and recomputing a table from its
copies finds a planted change."""

import filecmp
from datetime import date, datetime

from fno.global_cues import wiring
from fno.global_cues.collector import CueCollector
from fno.global_cues.job import GAPS_FILE, OVERLAP_FILE, CueChecks
from fno.global_cues.snapshot_log import SnapshotLog
from fno.global_cues.table import NSE_OPEN, CueTable
from fno.global_cues.verify import CueTableVerifier
from fno.models import IST
from fno.storage.raw_store import LocalFolderStore
from tests.global_cues.fakes import FakeSource, fake_file

TABLES = wiring.build_tables()


def test_every_cue_has_history_from_2007_and_every_row_names_a_logged_copy():
    log = SnapshotLog(wiring.SNAPSHOT_LOG_FOLDER)
    for source in wiring.SOURCES:
        rows = TABLES[source.cue].rows()
        assert rows and rows[0]["value_date"] <= "2018-07-10", source.cue
        logged = log.paths_by_sha256(source.cue)
        assert {r["source_sha256"] for r in rows} <= set(logged), source.cue


def test_backfilled_rows_are_exactly_those_seen_after_their_first_nse_open():
    after = wiring.next_nse_session(wiring.storage.build_session_calendar())
    for source in wiring.SOURCES:
        for r in TABLES[source.cue].rows():
            first_use = datetime.combine(after(date.fromisoformat(r["value_date"])), NSE_OPEN, tzinfo=IST)
            seen_late = datetime.fromisoformat(r["first_seen_at"]) >= first_use
            assert r["provenance"] == ("backfilled" if seen_late else "live"), (source.cue, r["value_date"])
    assert {r["provenance"] for r in TABLES["brent"].rows()} == {"backfilled"}  # EIA publishes weekly


def test_the_committed_checks_are_what_the_code_writes(tmp_path):
    CueChecks(TABLES, tmp_path).write()
    for name in (GAPS_FILE, OVERLAP_FILE):
        assert filecmp.cmp(tmp_path / name, wiring.CHECKS_FOLDER / name, shallow=False), name


def test_rbi_and_fbil_never_differ_where_both_publish():
    kinds = {line.split(",")[1] for line in (wiring.CHECKS_FOLDER / OVERLAP_FILE).read_text().splitlines()[1:]}
    assert kinds <= {"only_fbil", "only_rbi"}


def test_recomputing_from_the_copies_finds_a_planted_change(tmp_path):
    store, log = LocalFolderStore(tmp_path / "raw"), SnapshotLog(tmp_path / "log")
    source = FakeSource({"a.csv": fake_file(("2026-10-13", 1.0), ("2026-10-14", 2.0))})
    seen = datetime(2026, 10, 15, 6, 0, tzinfo=IST)
    result = CueCollector(None, store, log, lambda: seen).collect(source, date(2026, 1, 1), date(2026, 12, 31))
    table = CueTable(tmp_path / "tables", "fake", lambda d: d)
    table.merge(result.values, seen)
    verifier = CueTableVerifier(store, log)
    assert verifier.problems(source, table.rows()) == []
    planted = table.rows()
    planted[1]["value"] = "2.5"
    assert verifier.problems(source, planted) == ["fake 2026-10-14: table 2.5, archived copy 2.0"]
    planted[0]["source_sha256"] = "0" * 64
    assert "fake 2026-10-13: no logged copy with SHA-256 000000000000" in verifier.problems(source, planted)

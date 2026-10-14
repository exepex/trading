"""Story C4: failures are logged in `journal/<book>/validity_failures.csv` (one row per failed check, header once,
nothing for a pass), and the capture a decision is checked against is the one the day's committed common pack names."""

import csv

from fno.checks.schedule import PackSnapshotSchedule
from fno.checks.validity_capture import PackCaptures
from fno.checks.validity_failures import COLUMNS, ValidityFailureLog
from fno.desk.pack_store import PackStore
from tests.checks.builders import committed_record, pack_of
from tests.checks.validity_builders import DAY, check, committed_store, proposal


def test_each_failed_check_is_one_row_and_a_pass_writes_nothing(tmp_path):
    log = ValidityFailureLog(tmp_path)
    log.append(DAY, check())
    assert not log.path("book1_rules").exists()
    log.append(DAY, check(proposal(open_before=3, risk_verdicts_ok=False)))
    log.append(DAY, check(record=None))
    path = tmp_path / "journal" / "book1_rules" / "validity_failures.csv"
    assert log.path("book1_rules") == path
    lines = path.read_text(encoding="utf-8").splitlines()
    assert lines[0] == ",".join(COLUMNS) and sum(line.startswith("day,") for line in lines) == 1
    rows = list(csv.DictReader(lines))
    assert [r["check"] for r in rows] == ["open_trades", "risk_verdicts", "evidence"]
    assert rows[0]["day"] == "2026-10-14" and rows[0]["opportunity_id"] == "c4-sf-v1:2026-10-27"
    assert "3 open before, limit 3" in rows[0]["reason"]


def test_the_capture_is_the_one_the_committed_pack_names(tmp_path):
    store, packs = committed_store(), PackStore(tmp_path)
    captures = PackCaptures(packs, PackSnapshotSchedule())
    assert captures.record(DAY) is None  # no pack written for the day
    packs.write_common(pack_of(store, DAY))
    found = captures.record(DAY)
    expected = committed_record(store, DAY, "exec")
    assert (found.snapshot_id, found.csv_sha256, found.meta_sha256) == (
        expected.snapshot_id, expected.csv_sha256, expected.meta_sha256,
    )  # fmt: skip
    assert check(store=store, record=found).ok


def test_a_pack_that_differs_from_its_hash_names_nothing(tmp_path):
    store, packs = committed_store(), PackStore(tmp_path)
    path = packs.write_common(pack_of(store, DAY))
    path.write_bytes(path.read_bytes().replace(b'"exec"', b'"other"'))
    assert PackCaptures(packs, PackSnapshotSchedule()).record(DAY) is None

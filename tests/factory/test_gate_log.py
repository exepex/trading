"""The gate log's guard (story R1a, criterion 2): rows are only ever appended; a planted edit or deletion is refused."""

import pytest

from fno.factory.gate_log import GateLog, GateLogError, GateRow
from fno.factory.staging import FactoryGit

from .helpers import commit, init_repo


def idea(trial, numbers=""):
    return GateRow(trial, "G0", "idea", "2026-10-16", "abc", numbers)


@pytest.fixture
def log(tmp_path):
    init_repo(tmp_path)
    gates = GateLog(tmp_path, FactoryGit(tmp_path))
    gates.append(idea("1"))
    commit(tmp_path, "first gate row")
    return gates


def test_append_keeps_every_earlier_row(log):
    before = log.file.read_text()
    log.append(idea("2", "backfilled=yes"))
    assert log.file.read_text().startswith(before)
    assert before.startswith("trial_id,gate,outcome,on,commit,numbers\n")
    assert [row.trial_id for row in log.rows()] == ["1", "2"] and log.last("2").numbers == "backfilled=yes"
    assert log.last("9") is None


@pytest.mark.parametrize("edit", [lambda t: t.replace("2026-10-16", "2026-10-01"), lambda t: t.splitlines()[0] + "\n"])
def test_a_planted_edit_or_deletion_in_the_working_file_is_refused(log, edit):
    log.file.write_text(edit(log.file.read_text()))
    assert log.history_problems()
    with pytest.raises(GateLogError, match="not append-only"):
        log.append(idea("2"))


def test_a_committed_edit_is_still_found_in_history(log, tmp_path):
    log.file.write_text(log.file.read_text().replace(",abc,", ",def,"))
    commit(tmp_path, "rewrite a past row")
    assert log.history_problems() == ["version 1 does not keep version 0's rows unchanged"]
    with pytest.raises(GateLogError, match="not append-only"):
        log.require_append_only()


@pytest.mark.parametrize(
    ("row", "message"),
    [
        (GateRow("x", "G0", "idea", "2026-10-16", "abc", ""), "not a ledger trial number"),
        (GateRow("2", "G9", "idea", "2026-10-16", "abc", ""), "unknown gate"),
        (GateRow("2", "G0", "passed", "2026-10-16", "abc", ""), "unknown gate"),
        (GateRow("2", "G0", "idea", "2026-10-16", "abc", "net=1,2"), "not k=v;k=v"),
    ],
)
def test_a_bad_row_is_refused(log, row, message):
    with pytest.raises(GateLogError, match=message):
        log.append(row)
    assert len(log.rows()) == 1


def test_wrong_columns_are_refused(log):
    log.file.write_text(log.file.read_text().replace("numbers", "net"))
    with pytest.raises(GateLogError, match="columns must be"):
        log.rows()


def test_a_malformed_earlier_row_refuses_a_new_append(log, tmp_path):
    log.file.write_text(log.file.read_text() + "2,G9,idea,2026-10-16,abc,\n")
    commit(tmp_path, "a malformed row, committed: the history stays append-only")
    before = log.file.read_text()
    with pytest.raises(GateLogError, match="unknown gate 'G9'"):
        log.append(idea("3"))
    assert log.file.read_text() == before

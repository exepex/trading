"""O9b step 2, A14's margins in Drive: the table moves and reads back equal through the real wiring; C2, C4 and A14's
own log refuse by name when Drive cannot give the table (fail closed, no fallback: owner, 23 Oct 2026); a run day's
evidence CSV is written once with a receipt whose SHA-256 is the one its factor row names. Made-up figures."""

from __future__ import annotations

import itertools
from datetime import date

import pytest

from fno.checks.validity_margin import MarginFile, MarginProblem
from fno.nse_margins import wiring
from fno.nse_margins.margin_log import MarginLog, MarginLogConflict
from fno.nse_margins.stress_evidence import Evidence
from fno.risk.inputs import RiskInputError, TradeTerms
from fno.risk.margin_age import DaysOld
from fno.risk.margins import MARGIN_COLUMNS, MarginTable
from fno.storage import data_wiring
from fno.storage.moving import MoveRefused
from fno.storage.raw_store import LocalFolderStore
from fno.storage.receipted_rows import ReceiptedRowLog
from fno.storage.row_log import TableFileBroken
from fno.storage.table_source import ReceiptedTable

DAY = date(2026, 10, 16)
TABLE = ",".join(MARGIN_COLUMNS) + "\nSF,200,40000.00,0,0,test calculator,2026-10-15\n"
CFG = {"risk": {"margins": {"table": "margins/margins"}}}


@pytest.fixture
def repo(tmp_path, monkeypatch):
    """A checkout with the margins file and an evidence CSV, Drive as a local folder, receipts under the checkout."""
    drive = LocalFolderStore(tmp_path / "drive")
    (tmp_path / wiring.STRESS_EVIDENCE).mkdir(parents=True)
    (tmp_path / wiring.MARGINS_FILE).write_text(TABLE)
    (tmp_path / wiring.STRESS_EVIDENCE / "stress_evidence_2026-10-18.csv").write_text("scope,needed_factor\nall,1.2\n")
    monkeypatch.setattr(data_wiring, "build_owner_drive", lambda env: drive)
    monkeypatch.setattr(data_wiring, "REPOSITORY", tmp_path)
    runs = itertools.count(1)  # one run id per series, later each time, as separate runs' are
    monkeypatch.setattr(data_wiring, "new_run_id", lambda: f"20261023T{next(runs):06d}Z-aaaaaa")
    return tmp_path


def test_the_table_and_evidence_move_and_c2_and_c4_then_read_drive(repo):
    lines = wiring.move_margins_to_drive(CFG, repo)
    assert [line.split(":")[0] for line in lines] == [wiring.MARGINS_FILE, "stress_evidence_2026-10-18.csv"]
    assert all("moved to Drive and read back equal" in line for line in lines)
    (repo / wiring.MARGINS_FILE).unlink()  # readers no longer read the repository
    table = data_wiring.build_data_table("margins/margins")
    assert MarginTable(table, DaysOld(7), 65).margin(TradeTerms("SF", 200.0, 1), DAY) == 40000.0
    assert MarginFile(table).rows()[0]["source"] == "test calculator"
    assert receipts(repo, "stress-evidence/2026-10-18") == 1


def test_c2_c4_and_the_log_refuse_by_name_when_drive_cannot_give_the_table():
    def unreachable() -> ReceiptedRowLog:
        raise ConnectionError("drive down")  # requests' errors are OSError

    table = ReceiptedTable(unreachable, "margins/margins")
    with pytest.raises(RiskInputError, match=r"margins/margins: its Drive copy could not be read \(ConnectionError\)"):
        MarginTable(table, DaysOld(7), 65).margin(TradeTerms("SF", 200.0, 1), DAY)
    with pytest.raises(MarginProblem, match="could not be read"):
        MarginFile(table).rows()
    with pytest.raises(MarginLogConflict, match="could not be read"):
        MarginLog(table, None).existing()


def test_an_empty_drive_table_is_missing_for_every_reader(repo):
    table = data_wiring.build_data_table("margins/margins")  # no receipt: nothing moved yet
    with pytest.raises(RiskInputError, match="margins/margins is missing"):
        MarginTable(table, DaysOld(7), 65).margin(TradeTerms("SF", 200.0, 1), DAY)


def test_a_run_days_evidence_is_saved_once_with_the_factor_rows_sha256(repo):
    evidence = Evidence("scope,needed_factor\nall,1.25\n", "session,file,sha256\n", "# summary\n")
    save = wiring.build_evidence_saver()
    save(DAY, evidence.csv_text.encode("utf-8"))
    save(DAY, evidence.csv_text.encode("utf-8"))  # a rerun with the same bytes writes nothing
    (receipt,) = (repo / "receipts/data/margins/stress-evidence" / DAY.isoformat()).glob("*.sha256")
    assert receipt.read_text().split()[0] == evidence.sha256  # factor row -> receipt -> Drive bytes


def test_a_table_grown_since_its_move_is_caught_up_and_a_different_one_is_refused(repo):
    """The merge-day re-run (A14/C2/C4 owner's review, blocking 1): main's job appends rows every morning."""
    wiring.move_margins_to_drive(CFG, repo)
    with open(repo / wiring.MARGINS_FILE, "a") as f:
        f.write("SC,200,30000.00,0,0,test calculator,2026-10-16\n")
    assert "caught up and read back equal" in wiring.move_margins_to_drive(CFG, repo)[0]
    table = MarginTable(data_wiring.build_data_table("margins/margins"), DaysOld(7), 65)
    assert table.margin(TradeTerms("SC", 200.0, 1), DAY) == 30000.0 and receipts(repo, "margins") == 2
    (repo / wiring.MARGINS_FILE).write_text(TABLE.replace("40000.00", "41000.00"))  # not a start of Drive's table
    with pytest.raises(MoveRefused, match="Drive already holds other bytes"):
        wiring.move_margins_to_drive(CFG, repo)
    assert receipts(repo, "margins") == 2


def test_a_table_without_its_last_new_line_is_refused_and_nothing_is_written(repo):
    """Blocking 2: parts are joined end to end, so a last row without its new line would swallow the next part's."""
    (repo / wiring.MARGINS_FILE).write_text(TABLE.rstrip("\n"))
    with pytest.raises(TableFileBroken, match="does not end with a new line"):
        wiring.move_margins_to_drive(CFG, repo)
    assert receipts(repo, "margins") == 0


def test_an_evidence_csv_differing_from_drives_copy_is_refused_never_replaced(repo):
    """Its factor row names its SHA-256, so a disagreement goes to a person (owner's review note 1)."""
    wiring.move_margins_to_drive(CFG, repo)
    (repo / wiring.STRESS_EVIDENCE / "stress_evidence_2026-10-18.csv").write_text("scope,needed_factor\nall,9.9\n")
    with pytest.raises(MoveRefused, match="stress_evidence_2026-10-18.csv: Drive already holds other bytes"):
        wiring.move_margins_to_drive(CFG, repo)
    assert receipts(repo, "stress-evidence/2026-10-18") == 1


def receipts(repo, folder: str) -> int:
    return len(list((repo / "receipts/data/margins" / folder).glob("*.sha256")))

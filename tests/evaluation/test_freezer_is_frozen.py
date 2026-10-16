"""Response 230 (BR1a follow-up): S1's freeze hashes the freezer itself. `definition.py` holds S1's definition and
the real-money gate's requirement, so an edit to it after a freeze is caught like any frozen file."""

from datetime import date

from fno.config import ROOT
from fno.evaluation.freeze import ProtocolFreezer, frozen_targets
from fno.evaluation.order import verify
from fno.playbook.history import PlaybookGit
from tests.evaluation.builders import DRAFT, decided, protocol_repo, small_frozen_files
from tests.playbook.builders import commit_all

FREEZER = ("fno/evaluation/definition.py", "fno/evaluation/freeze.py", "fno/evaluation/order.py")


def test_s1s_frozen_files_list_the_freezer():
    assert set(FREEZER) <= set(frozen_targets(DRAFT))


def test_a_frozen_versions_verify_fails_when_the_definition_changes(tmp_path):
    text = small_frozen_files(decided()).replace("`fno/scoring.py`", "`fno/scoring.py`, `fno/evaluation/definition.py`")
    protocol_repo(tmp_path, text)
    (tmp_path / FREEZER[0]).parent.mkdir(parents=True, exist_ok=True)
    (tmp_path / FREEZER[0]).write_bytes((ROOT / FREEZER[0]).read_bytes())
    commit_all(tmp_path, "the freezer's definition")
    ProtocolFreezer(tmp_path, PlaybookGit(tmp_path)).freeze(date(2026, 10, 21))
    assert verify(tmp_path) == []
    edited = (tmp_path / FREEZER[0]).read_text().replace("requires_gate=True", "requires_gate=False")
    (tmp_path / FREEZER[0]).write_text(edited)
    assert verify(tmp_path) == [f"v1: {FREEZER[0]} changed after the freeze (a change is a new version)"]

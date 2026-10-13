"""Protocol version 2's freeze (orchestrator, after judge 47 addendum 3): the check covers the v2 code itself, not only
the protocol text, and refuses a live capture when any frozen file changed."""

from pathlib import Path

import pytest

from fno.config import ROOT
from fno.forecast.freeze import file_sha256
from fno.forecast.freeze_v2 import (
    FREEZE_V2,
    PROTOCOL_V2,
    NotFrozen,
    NotYetFrozen,
    read_version_freeze,
    require_version_frozen,
)
from fno.research_engine.ledger import Git, Ledger
from tests.forecast.test_freeze import _commit, _freeze_text, _git

V2_CODE = ("live_pack.py", "live_history.py", "closes_source.py", "schema_v2.py", "capture.py", "freeze_v2.py",
           "history.py", "baselines.py", "models.py", "book1_method.py", "baseline_wiring.py", "cli.py")  # fmt: skip


@pytest.fixture
def repo(tmp_path):
    _git(tmp_path, "init", "-q")
    protocol = tmp_path / PROTOCOL_V2
    protocol.parent.mkdir(parents=True)
    protocol.write_text("# Protocol v2\n")
    code = tmp_path / "fno" / "forecast" / "live_pack.py"
    code.parent.mkdir(parents=True)
    code.write_text("CUTOFF = '15:00:00'\n")
    before = _commit(tmp_path, "protocol")
    hashes = {PROTOCOL_V2: file_sha256(protocol), "fno/forecast/live_pack.py": file_sha256(code)}
    (tmp_path / FREEZE_V2).write_text(_freeze_text(before, hashes))
    return tmp_path, _commit(tmp_path, "freeze")


def test_a_commit_after_the_v2_freeze_passes(repo):
    root, frozen = repo
    (root / "notes.md").write_text("later\n")
    assert require_version_frozen(root, _commit(root, "later")).protocol_commit != frozen


def test_an_edit_to_frozen_v2_code_is_refused(repo):
    root, _ = repo
    (root / "fno" / "forecast" / "live_pack.py").write_text("CUTOFF = '15:00:01'\n")  # the judge's plant
    with pytest.raises(NotFrozen, match="live_pack.py"):
        require_version_frozen(root, _commit(root, "late cutoff"))


def test_no_v2_record_means_not_yet_frozen(tmp_path):
    with pytest.raises(NotYetFrozen):
        require_version_frozen(tmp_path, "0" * 40)


def test_the_repository_v2_freeze_holds_and_covers_the_v2_code():
    freeze = require_version_frozen(ROOT, Git(ROOT).head())
    frozen = set(freeze.hashes)
    assert {f"fno/forecast/{name}" for name in V2_CODE} <= frozen
    assert {str(p.relative_to(ROOT)) for p in (ROOT / "fno" / "forecast").glob("*.py")} <= frozen
    golden = {str(p.relative_to(ROOT)) for p in (ROOT / "research/forecasts/v2/golden").rglob("*") if p.is_file()}
    assert golden and golden <= frozen and "tools/forecast_live_golden.py" in frozen
    assert read_version_freeze((ROOT / FREEZE_V2).read_text(), PROTOCOL_V2) == freeze


def test_the_v2_ledger_trials_carry_the_protocol_commit():
    freeze = require_version_frozen(ROOT, Git(ROOT).head())
    rows = [r for r in Ledger(Path(ROOT)).rows() if r["experiment"] == "forecasts-v2"]
    assert [r["trial_id"] for r in rows] == ["37", "38", "39", "40", "41"]
    assert {r["protocol_commit"] for r in rows} == {freeze.protocol_commit}
    assert {r["protocol_path"] for r in rows} == {PROTOCOL_V2}

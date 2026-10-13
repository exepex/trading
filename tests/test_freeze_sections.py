"""G1 v3's freeze is split by consumer (orchestrator, after judge 64): one FREEZE_v3.md, one section per job. A change
to a question-5 scoring file fails the scoring job's check but not the panel job's, and the reverse."""

import pytest

from fno.forecast.freeze import NotFrozen, file_sha256
from fno.forecast.freeze_v2 import NotYetFrozen
from fno.freeze_sections import FORECAST_SCORES, FREEZE_V3, PANEL_DAYS, PROTOCOL_V3, require_section_frozen
from tests.forecast.test_freeze import _commit, _git

PANEL_FILE, Q5_FILE = "fno/pipeline/panel_days.py", "fno/forecast_scoring/q5_thresholds.py"


def _rows(root, *paths) -> str:
    return "| File | SHA-256 |\n|---|---|\n" + "".join(f"| `{p}` | `{file_sha256(root / p)}` |\n" for p in paths)


@pytest.fixture
def repo(tmp_path):
    _git(tmp_path, "init", "-q")
    for path, text in ((PROTOCOL_V3, "# v3\n"), (PANEL_FILE, "PANEL = 1\n"), (Q5_FILE, "LIVE = 'pack'\n")):
        (tmp_path / path).parent.mkdir(parents=True, exist_ok=True)
        (tmp_path / path).write_text(text)
    protocol = _commit(tmp_path, "protocol v3")
    (tmp_path / FREEZE_V3).write_text(
        f"# Freeze v3\n\nProtocol commit: `{protocol}`\n\n"
        f"## Checked by `{PANEL_DAYS}`\n\n{_rows(tmp_path, PROTOCOL_V3, PANEL_FILE)}\n"
        f"## Checked by `{FORECAST_SCORES}`\n\n{_rows(tmp_path, PROTOCOL_V3, Q5_FILE)}"
    )
    _commit(tmp_path, "freeze v3")
    return tmp_path


def _check(root, section):
    return require_section_frozen(root, _git(root, "rev-parse", "HEAD"), section)


def test_both_sections_hold_after_the_freeze(repo):
    assert _check(repo, PANEL_DAYS).hashes.keys() == {PROTOCOL_V3, PANEL_FILE}
    assert _check(repo, FORECAST_SCORES).hashes.keys() == {PROTOCOL_V3, Q5_FILE}


def test_a_q5_change_fails_scoring_but_not_the_panel_job(repo):
    (repo / Q5_FILE).write_text("LIVE = 'panel'\n")  # the judge's swap
    _commit(repo, "planted")
    assert _check(repo, PANEL_DAYS)
    with pytest.raises(NotFrozen, match="forecast-scores's frozen files changed .*q5_thresholds"):
        _check(repo, FORECAST_SCORES)


def test_a_panel_change_fails_the_panel_job_but_not_scoring(repo):
    (repo / PANEL_FILE).write_text("PANEL = 2\n")
    _commit(repo, "planted")
    assert _check(repo, FORECAST_SCORES)
    with pytest.raises(NotFrozen, match="panel-days's frozen files changed .*panel_days"):
        _check(repo, PANEL_DAYS)


def test_a_protocol_change_fails_both(repo):
    (repo / PROTOCOL_V3).write_text("# v3, edited\n")
    _commit(repo, "planted")
    for section in (PANEL_DAYS, FORECAST_SCORES):
        with pytest.raises(NotFrozen):
            _check(repo, section)


def test_no_record_is_not_yet_frozen_and_a_missing_section_is_refused(tmp_path, repo):
    with pytest.raises(NotYetFrozen):
        require_section_frozen(tmp_path / "empty", "0" * 40, PANEL_DAYS)
    with pytest.raises(NotFrozen, match="no section"):
        _check(repo, "other-job")

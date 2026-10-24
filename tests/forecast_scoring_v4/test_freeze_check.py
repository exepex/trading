"""The v4 freeze check (protocol section 10; the freeze plan, response 287): the record's table lists every
byte-checked file with its SHA-256, and the check finds every change, removal and addition since."""

import shutil
from pathlib import Path

from fno.forecast_scoring.v4 import freeze_check

ROOT = Path(__file__).resolve().parents[2]


def test_the_list_covers_the_protocol_g7_g8_a16_and_m1_and_records_the_shared_files():
    listed = freeze_check.byte_checked(ROOT)
    for path in ("research/forecasts/PROTOCOL_v4.md", "fno/forecast_v4/terms.py", "fno/forecast_v4_rules/rules.py",
                 "fno/forecast_scoring/v4/slot_file.py", "fno/forecast_scoring/v4/freeze_check.py",
                 "fno/intraday/session_rv.py", "fno/weather/colour.py", "tests/fixtures/forecast_v4/v4_golden.json",
                 "tools/v4_claim_thresholds.py", "research/forecasts/v4_vix_null.json"):  # fmt: skip
        assert path in listed, path
    assert not any("__pycache__" in p for p in listed)
    assert "fno/constants.py" not in listed and "- `fno/constants.py`" in freeze_check.recorded()


def test_the_list_covers_the_pack_the_iv30_files_and_the_ai_books_and_records_only_shared_files():
    """Story G6 freeze, criterion 1: G10's pack (V2's IV30 input, day labels, deadline), G1 v2's IV30 files and G11's
    AI files are byte-checked; the shared files stay recorded only, `iv30.py` no longer among them."""
    listed = freeze_check.byte_checked(ROOT)
    for path in ("fno/v4_pack/model.py", "fno/v4_pack/release_run.py", "fno/v4_pack/deadline.py",
                 "fno/research_engine/live_features.py", "fno/forecast/iv30.py", "fno/ai/v4_rows.py",
                 "fno/ai/scoring_gate.py", "fno/ai/outcome.py", "fno/ai/stop_rule.py",
                 "fno/ai/versions.py"):  # fmt: skip
        assert path in listed, path
    for pattern in ("fno/ai/v4_*.py", "agents/forecast/book2_hybrid_v2.md", "agents/forecast/book3_ai_v2.md"):
        assert pattern in freeze_check.BYTE_CHECKED_GLOBS, pattern  # G11's, matched once they are on main
    shared = set(freeze_check.RECORDED_NOT_CHECKED)
    assert not shared & set(listed) and "fno/forecast/iv30.py" not in shared
    assert {"fno/constants.py", "fno/desk/settlement.py", "fno/research_engine/implied_vol.py"} <= shared
    assert not any(p.startswith(("fno/ai/book", "fno/ai/cli", "fno/weather/cli")) for p in listed)  # not deciding


def test_an_empty_byte_checked_folder_adds_nothing(tmp_path):
    (tmp_path / "fno" / "v4_pack").mkdir(parents=True)
    assert freeze_check.byte_checked(tmp_path) == []


def test_a_fresh_table_shows_no_problem_on_this_repository():
    assert freeze_check.problems(ROOT, freeze_check.table(ROOT)) == []


def test_a_changed_a_removed_and_an_added_file_are_each_found(tmp_path):
    for path in ("fno/forecast_v4/terms.py", "fno/forecast_v4/loss.py", "research/forecasts/PROTOCOL_v4.md"):
        (tmp_path / path).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(ROOT / path, tmp_path / path)
    record = freeze_check.table(tmp_path)
    assert freeze_check.problems(tmp_path, record) == []
    (tmp_path / "fno/forecast_v4/terms.py").write_text("# edited\n", encoding="utf-8")
    (tmp_path / "fno/forecast_v4/loss.py").unlink()
    (tmp_path / "fno/forecast_v4/new_rule.py").write_text("X = 1\n", encoding="utf-8")
    assert freeze_check.problems(tmp_path, record) == [
        "fno/forecast_v4/loss.py: gone since the freeze",
        "fno/forecast_v4/terms.py: changed since the freeze (a change is a new version, never an edit)",
        "fno/forecast_v4/new_rule.py: added after the freeze",
    ]


def test_once_the_record_exists_the_repository_matches_it():
    record = ROOT / "research" / "forecasts" / "FREEZE_v4.md"
    if record.exists():
        assert freeze_check.problems(ROOT, record.read_text(encoding="utf-8")) == []
    else:  # before the freeze commit the protocol is still a draft
        assert "**Status: DRAFT, not frozen.**" in (ROOT / "research/forecasts/PROTOCOL_v4.md").read_text()

"""The v4 freeze check (protocol section 10; the freeze plan, response 287; story G6 freeze, criteria 1 and 12): the
record's tables list every byte-checked file with its SHA-256 and every recorded file with its SHA-256 and lock; the
check finds every change, removal and addition since, and names recorded files that changed (drift, not a break)."""

import shutil
from pathlib import Path

from fno.forecast_scoring.v4 import freeze_check
from fno.forecast_scoring.v4.freeze_classes import BYTE_CHECKED_GLOBS, NOT_DECIDING, RECORDED

ROOT = Path(__file__).resolve().parents[2]


def test_the_list_covers_the_protocol_g7_g8_a16_and_m1():
    listed = freeze_check.byte_checked(ROOT)
    for path in ("research/forecasts/PROTOCOL_v4.md", "fno/forecast_v4/terms.py", "fno/forecast_v4_rules/rules.py",
                 "fno/forecast_scoring/v4/slot_file.py", "fno/forecast_scoring/v4/freeze_check.py",
                 "fno/intraday/session_rv.py", "fno/weather/colour.py", "tests/fixtures/forecast_v4/v4_golden.json",
                 "tools/v4_claim_thresholds.py", "research/forecasts/v4_vix_null.json"):  # fmt: skip
        assert path in listed, path
    assert not any("__pycache__" in p for p in listed)


def test_the_pack_the_rate_and_g11s_v4_files_are_byte_checked_and_shared_files_only_recorded():
    """Criterion 1: v4's own files byte-checked; shared files that decide a v4 value recorded (judge 597 SF3)."""
    listed = set(freeze_check.byte_checked(ROOT))
    for path in ("fno/v4_pack/model.py", "fno/v4_pack/release_run.py", "fno/v4_pack/deadline.py",
                 "fno/forecast_v4/pricing.py", "fno/quotes/v4_extras.py", "fno/ai/v4_rows.py"):  # fmt: skip
        assert path in listed, path
    for pattern in ("fno/ai/v4_*.py", "agents/forecast/book2_hybrid_v2.md", "agents/forecast/book3_ai_v2.md"):
        assert pattern in BYTE_CHECKED_GLOBS, pattern
    for path in ("fno/constants.py", "fno/research_engine/live_features.py", "fno/forecast/iv30.py",
                 "fno/intraday/candle_rv_table.py", "fno/ai/versions.py", "fno/ai/outcome.py"):  # fmt: skip
        assert path in RECORDED and path not in listed, path
    assert not set(RECORDED) & listed and not set(NOT_DECIDING) & (listed | set(RECORDED))
    assert all(reason.strip() for reason in (*RECORDED.values(), *NOT_DECIDING.values()))


def test_an_empty_byte_checked_folder_adds_nothing_and_a_pattern_matching_nothing_is_named(tmp_path):
    (tmp_path / "fno" / "v4_pack").mkdir(parents=True)
    (tmp_path / "fno" / "v4_pack" / "keep.txt").write_text("not python", encoding="utf-8")
    assert freeze_check.byte_checked(tmp_path) == []
    missing = freeze_check.unmatched(tmp_path)
    assert "fno/v4_pack/*.py" in missing and "fno/constants.py" in missing


def test_today_only_g11s_files_still_to_merge_match_nothing():
    """The freeze tool refuses while this is not empty: G11's prompts and v4-only files land before the freeze."""
    assert set(freeze_check.unmatched(ROOT)) <= {"agents/forecast/book2_hybrid_v2.md", "agents/forecast/book3_ai_v2.md"}


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


def test_the_recorded_tables_hold_each_shared_file_with_its_lock_and_g11s_files_apart():
    text = freeze_check.recorded(ROOT)
    head, ai = text.split("### AI registration (G11's shared files)")
    assert (
        f"| `fno/constants.py` | `{freeze_check.sha256(ROOT / 'fno/constants.py')}` | {RECORDED['fno/constants.py']} |"
        in head
    )
    assert "`fno/ai/versions.py`" in ai and "`fno/ai/" not in head


def test_a_recorded_file_changed_since_the_freeze_is_named_but_breaks_nothing(tmp_path):
    for path in ("fno/constants.py", "fno/analytics.py"):
        (tmp_path / path).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(ROOT / path, tmp_path / path)
    record = freeze_check.recorded(tmp_path)
    assert freeze_check.drift(tmp_path, record) == []
    (tmp_path / "fno/analytics.py").write_text("# edited\n", encoding="utf-8")
    assert freeze_check.drift(tmp_path, record) == [
        f"recorded file changed since the freeze: fno/analytics.py ({RECORDED['fno/analytics.py']})"
    ]
    assert freeze_check.problems(tmp_path, record) == []  # the byte-checked table is apart: drift is never a break


def test_once_the_record_exists_the_repository_matches_it():
    record = ROOT / "research" / "forecasts" / "FREEZE_v4.md"
    if record.exists():
        assert freeze_check.problems(ROOT, record.read_text(encoding="utf-8")) == []
    else:  # before the freeze commit the protocol is still a draft
        assert "**Status: DRAFT, not frozen.**" in (ROOT / "research/forecasts/PROTOCOL_v4.md").read_text()

"""Story G6 freeze, criterion 9: the record's disclosure (protocol section 8) lists every back-fill source with its
days, row count, method hashes and the SHA-256 of its back-fill rows; live rows, reports and Drive back-fills made on or
before the freeze day apart; and "none" for an empty part. Fixture folders, then the real repository."""

import hashlib
import json
from datetime import date
from pathlib import Path

from fno.forecast_scoring.v4.freeze_disclosure import (
    NONE,
    csv_rows,
    disclosure,
    drive_backfills,
    reports_through,
    weather_rows,
)

ROOT = Path(__file__).resolve().parents[2]
HEADER = "day,value,status,label,forecaster_version,kind,slot,method_sha256,inputs_sha256,pack_sha256,made_at"
FREEZE = date(2026, 10, 25)


def _line(day: str, label: str, method: str = "a" * 64) -> str:
    return f"{day},0.04,ok,{label},1,rule,rules,{method},{'b' * 64},,"


def _csv(root: Path, forecaster: str, lines: list[str]) -> Path:
    path = root / "research/forecasts/v4" / forecaster / "v6_abs_move_2pct_next_session.csv"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join([HEADER, *lines]) + "\n", encoding="utf-8")
    return path


def test_a_mixed_file_discloses_its_backfill_rows_and_its_live_rows_apart(tmp_path):
    back = [_line("2017-01-03", "backfill_exploratory"), _line("2026-10-15", "backfill_exploratory")]
    live = [_line("2026-10-22", "live"), _line("2026-10-26", "live")]  # the second one is after the freeze
    _csv(tmp_path, "base_rate", [*back, *live])
    (found,) = csv_rows(tmp_path, "backfill_exploratory")
    assert (found.first, found.last, found.count, found.methods) == ("2017-01-03", "2026-10-15", 2, ("a" * 64,))
    assert found.sha256 == hashlib.sha256(("\n".join([HEADER, *back]) + "\n").encode()).hexdigest()
    (before,) = csv_rows(tmp_path, "live", FREEZE)
    assert (before.first, before.last, before.count) == ("2026-10-22", "2026-10-22", 1)


def test_rows_made_by_two_methods_name_both(tmp_path):
    _csv(tmp_path, "v6_ewma_t4", [_line("2017-01-03", "backfill_exploratory", "c" * 64),
                                  _line("2017-01-04", "backfill_exploratory", "d" * 64)])  # fmt: skip
    assert csv_rows(tmp_path, "backfill_exploratory")[0].methods == ("c" * 64, "d" * 64)


def test_a_file_of_live_rows_only_has_no_backfill_line(tmp_path):
    _csv(tmp_path, "v1_close_blend", [_line("2026-10-22", "live")])
    assert csv_rows(tmp_path, "backfill_exploratory") == [] and len(csv_rows(tmp_path, "live", FREEZE)) == 1


def test_the_weather_day_files_are_one_source(tmp_path):
    for day, label in (("2017-01-03", "backfill_exploratory"), ("2026-10-19", "backfill_exploratory"),
                       ("2026-10-22", "live")):  # fmt: skip
        path = tmp_path / "research/forecasts/v4/weather" / day[:4] / f"{day}.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({"day": day, "label": label, "method_sha256": "e" * 64}), encoding="utf-8")
    (found,) = weather_rows(tmp_path, "backfill_exploratory")
    assert (found.source, found.first, found.last, found.count) == (
        "research/forecasts/v4/weather/*/*.json", "2017-01-03", "2026-10-19", 2)  # fmt: skip
    assert weather_rows(tmp_path, "live", date(2026, 10, 21)) == []


def test_reports_and_drive_receipts_are_listed_on_or_before_the_freeze(tmp_path):
    folder = tmp_path / "research/forecasts/v4_scores"
    folder.mkdir(parents=True)
    for name in ("2026-10-24.md", "2026-10-25.json", "2026-10-26.md", "look_stop_rule_review.json"):
        (folder / name).write_text("x", encoding="utf-8")
    assert reports_through(tmp_path, FREEZE) == [f"research/forecasts/v4_scores/{n}" for n in
                                                 ("2026-10-24.md", "2026-10-25.json")]  # fmt: skip
    receipt = tmp_path / "receipts/data/v4/records/backfill/21f62594/raw_implied/v2_to_2026-10-15.csv.sha256"
    receipt.parent.mkdir(parents=True)
    receipt.write_text(f"{'f' * 64}\t10\t2026-10-24T10:00:00+00:00\tv4\tid\n", encoding="utf-8")
    assert drive_backfills(tmp_path) == [f"| `{receipt.relative_to(tmp_path).as_posix()}` | `{'f' * 64}` |"]


def test_an_empty_repository_discloses_none_in_every_part(tmp_path):
    assert disclosure(tmp_path, FREEZE).count(NONE) == 4


def test_the_repository_discloses_g7s_and_m1s_backfills_and_the_pre_freeze_live_days():
    text = disclosure(ROOT, FREEZE)
    for source in ("base_rate/v6_abs_move_2pct_next_session.csv", "v7_vix_vs_mean20/", "weather_vix_v1/",
                   "research/forecasts/v4/weather/*/*.json"):  # fmt: skip
        assert source in text, source
    backfill, live = text.split("### Live rows")[0], text.split("### Live rows")[1].split("### G8")[0]
    assert "| 2017-01-03 |" in backfill and "2026-10-22" not in backfill and "| 2026-10-22 |" in live

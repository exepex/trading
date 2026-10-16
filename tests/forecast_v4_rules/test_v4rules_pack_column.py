"""G10 part 2's `pack_sha256` column in the v4 records (G7's records.py): its form check, G7's rows empty, and the
tolerant read of files written before the column existed (G7's and M1's committed CSVs need no rewrite)."""

from datetime import date
from pathlib import Path

import pytest

from fno.constants import V6_BIG_MOVE_1S
from fno.forecast_v4_rules import records
from fno.forecast_v4_rules.baselines import OK

ROOT = Path(__file__).resolve().parents[2]
DAY = date(2026, 10, 16)
AUDIT = dict(label="live", kind="rule", slot="reported", method_sha256="m", inputs_sha256="i", made_at="t")


def test_the_column_sits_right_after_the_inputs_hash():
    assert records.COLUMNS.index("pack_sha256") == records.COLUMNS.index("inputs_sha256") + 1


def test_a_pack_hash_is_empty_or_64_lowercase_hex():
    assert records.record(DAY, V6_BIG_MOVE_1S, OK, 0.5, **AUDIT).pack_sha256 == ""
    assert records.record(DAY, V6_BIG_MOVE_1S, OK, 0.5, pack_sha256="a" * 64, **AUDIT).pack_sha256 == "a" * 64
    for bad in ("a" * 63, "A" * 64, "g" * 64, " " + "a" * 64):
        with pytest.raises(records.InvalidRecord):
            records.record(DAY, V6_BIG_MOVE_1S, OK, 0.5, pack_sha256=bad, **AUDIT)


def test_a_file_without_the_column_reads_as_empty_and_compares_equal(tmp_path):
    old = tmp_path / "f" / f"{V6_BIG_MOVE_1S}.csv"
    old.parent.mkdir()
    header = [c for c in records.COLUMNS if c != "pack_sha256"]
    old.write_text(",".join(header) + "\n2026-10-16,0.5,ok,live,1,rule,reported,m,i,t\n")
    row = records.read(old)["2026-10-16"]
    assert row.pack_sha256 == "" and row.same_as(records.record(DAY, V6_BIG_MOVE_1S, OK, 0.5, **AUDIT))
    assert records.write(tmp_path, "f", V6_BIG_MOVE_1S, [records.record(DAY, V6_BIG_MOVE_1S, OK, 0.5, **AUDIT)]) == 0


def test_every_committed_v4_csv_still_reads_and_carries_no_pack_hash():
    files = list((ROOT / "research" / "forecasts" / "v4").glob("*/*.csv"))
    assert len(files) >= 16  # G7's 14 and M1's 2 forecaster folders' files
    for file in files:
        assert {r.pack_sha256 for r in records.read(file).values()} == {""}, file

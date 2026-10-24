"""Story G10 completion, criterion 11: the 14:30 overlap watch posts one line, counts only, when either the v4 capture
or A16's 14:30 mark shows any failure; nothing on a clean day or a day without a v4 capture; A16's `missed` row and a
missing row are both named (judge 580.1 minor 3: 23 Oct's 14:30 row exists with status `missed`)."""

import json
import shutil
from datetime import date

from fno.config import ROOT
from fno.v4_pack.overlap import OverlapWatch

DAY = date(2026, 10, 26)
HEADER = "session,mark,mark_ist,status,failures\n"


def watch(tmp_path, failures=(), a16="good,", attempts=1):
    v4 = tmp_path / "v4" / "2026" / "10"
    v4.mkdir(parents=True)
    for n in range(attempts):
        meta = {"failures": list(failures) if n == 0 else [], "recorded_contracts": 268, "expected_contracts": 270}
        (v4 / f"nifty_20261026_14300{n}.meta.json").write_text(json.dumps(meta))
    (v4 / "nifty_20261026.canonical").write_text(f"nifty_20261026_14300{attempts - 1}")
    if a16 is not None:
        slots = tmp_path / "intraday" / "slots" / "2026" / "10" / "26"
        slots.mkdir(parents=True)
        (slots / "nifty_20261026_1430.csv").write_text(HEADER + f"2026-10-26,2026-10-26T09:00:00+00:00,14:30,{a16}\n")
    return OverlapWatch(tmp_path / "v4", tmp_path / "intraday")


def test_a_clean_day_says_nothing(tmp_path):
    assert watch(tmp_path).line(DAY) is None


def test_two_v4_failures_with_a16_good_are_named_with_counts(tmp_path):
    line = watch(tmp_path, failures=("2026-10-27 22450 CE: GrowwAPIException (provider message withheld)",) * 2,
                 attempts=2).line(DAY)  # fmt: skip
    assert line == ("v4 14:30 overlap 2026-10-26: v4 capture 2 failure(s) in 2 attempt(s), 268 of 270 contracts in "
                    "the canonical one; A16's 14:30 mark good, failures: none (Groww's messages are withheld: see the "
                    "counts)")  # fmt: skip
    assert "22450" not in line  # counts only, never a contract or a quote


def test_a16_s_missed_row_and_a_missing_row_are_both_named(tmp_path):
    assert "A16's 14:30 mark missed, failures: not_taken" in watch(tmp_path / "a", a16="missed,not_taken").line(DAY)
    assert "missing (no row: A16's routine did not record it)" in watch(tmp_path / "b", a16=None).line(DAY)


def test_no_v4_capture_says_nothing(tmp_path):
    (tmp_path / "v4").mkdir()
    assert OverlapWatch(tmp_path / "v4", tmp_path / "intraday").line(DAY) is None


def test_the_real_23_oct_14_30_row_reads_as_missed(tmp_path):
    """A16's real committed row of 23 Oct (status missed, not_taken) beside a clean fixture capture of that day."""
    day = date(2026, 10, 23)
    v4 = tmp_path / "v4" / "2026" / "10"
    v4.mkdir(parents=True)
    (v4 / "nifty_20261023_143000.meta.json").write_text(json.dumps({"failures": []}))
    slots = tmp_path / "intraday" / "slots" / "2026" / "10" / "23"
    slots.mkdir(parents=True)
    shutil.copy(ROOT / "research/data/intraday/slots/2026/10/23/nifty_20261023_1430.csv", slots)
    assert "A16's 14:30 mark missed, failures: not_taken" in OverlapWatch(tmp_path / "v4", tmp_path / "intraday").line(
        day
    )

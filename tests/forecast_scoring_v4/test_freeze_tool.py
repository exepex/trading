"""Story G6 freeze, criteria 1, 3 and 9: the freeze tool refuses a dirty tree, a listed file or pattern that matches
nothing, and a v4 module that still reads the configured rate; it names the C library for the libm limit (judge 508)."""

from pathlib import Path

from fno.forecast_scoring.v4.freeze_check import rate_readers, unmatched
from tools.v4_freeze_table import platform_line, refusals

ROOT = Path(__file__).resolve().parents[2]


def test_every_refusal_is_named():
    found = refusals(ROOT, " M fno/forecast_v4/terms.py\n")
    assert found[0] == "uncommitted changes:  M fno/forecast_v4/terms.py"
    assert [f for f in found if f.startswith("matches no file: ")] == [f"matches no file: {p}" for p in unmatched(ROOT)]
    assert [f for f in found if f.startswith("reads the configured rate")] == [
        f"reads the configured rate (protocol 1.4: pricing.py only): {p}" for p in rate_readers(ROOT)
    ]


def test_a_clean_tree_with_every_file_and_no_reader_is_not_refused(tmp_path):
    assert refusals(tmp_path, "") == [f"matches no file: {p}" for p in unmatched(tmp_path)]  # an empty tree: only these


def test_the_platform_line_names_python_numpy_and_the_c_library():
    line = platform_line()
    assert line.startswith("Python 3.") and ", numpy " in line and ", C library " in line and "C library -," not in line

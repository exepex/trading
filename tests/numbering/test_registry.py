"""Story O12: registry rows, and the next number per category and per report."""

import pytest

from fno.numbering.categories import CLAUDE_RESPONSE, JUDGE_ADDENDUM, JUDGE_REPORT
from fno.numbering.registry import Row, append_row, next_number, read_rows, valid_stamp
from tests.numbering.helpers import HEADER


def test_an_empty_or_missing_registry_starts_at_one(tmp_path):
    assert read_rows(tmp_path / "none.csv") == []
    assert next_number(CLAUDE_RESPONSE, []) == "1"
    assert next_number(JUDGE_ADDENDUM, [], report="270") == "270.1"


def test_the_next_number_follows_the_highest_not_the_count_and_skips_malformed_ones():
    assert next_number(JUDGE_REPORT, ["1", "66", "66", "9", "x", "07", "500.1"]) == "67"


def test_addenda_have_one_sequence_per_report():
    taken = ["270.1", "270.2", "27.5", "2700.9", "270", "270.x"]
    assert next_number(JUDGE_ADDENDUM, taken, report="270") == "270.3"
    assert next_number(JUDGE_ADDENDUM, taken, report="27") == "27.6"
    assert next_number(JUDGE_ADDENDUM, taken, report="271") == "271.1"


def test_a_utc_stamp_must_have_its_full_shape():
    assert valid_stamp("2026-10-16T10:00:00Z")
    for wrong in ("2026-1-5T1:2:3Z", "2026-10-16T10:00:00", "2026-10-16 10:00:00Z", "2026-13-16T10:00:00Z", ""):
        assert not valid_stamp(wrong)


def test_blank_lines_a_byte_order_mark_and_an_empty_file_are_tolerated(tmp_path):
    path = tmp_path / "x.csv"
    path.write_text("\ufeff" + HEADER + "1,a,existing,\n\n")
    assert read_rows(path) == [Row("1", "a", "existing")]
    path.write_text("")
    append_row(path, Row("1", "a", "s", "2026-10-16T10:00:00Z"))
    assert read_rows(path) == [Row("1", "a", "s", "2026-10-16T10:00:00Z")]


def test_append_writes_the_header_once_and_quotes_commas(tmp_path):
    path = tmp_path / "numbers" / "x.csv"
    append_row(path, Row("1", "a,b", "s1", "2026-10-16T10:00:00Z"))
    append_row(path, Row("2", "c", "s2", "2026-10-16T10:00:01Z"))
    assert path.read_text().startswith(HEADER)
    assert read_rows(path) == [
        Row("1", "a,b", "s1", "2026-10-16T10:00:00Z"),
        Row("2", "c", "s2", "2026-10-16T10:00:01Z"),
    ]


@pytest.mark.parametrize("text", ["", "number,name\n", HEADER + "1,a,s\n", HEADER + "1,a,s,t,extra\n"])
def test_a_malformed_registry_is_refused(tmp_path, text):
    (tmp_path / "x.csv").write_text(text)
    with pytest.raises(ValueError):
        read_rows(tmp_path / "x.csv")


def test_append_after_a_hand_edit_without_a_last_line_break_keeps_rows_apart(tmp_path):
    path = tmp_path / "x.csv"
    path.write_text(HEADER + "1,a,existing,")
    append_row(path, Row("2", "b", "s", "2026-10-16T10:00:00Z"))
    assert [row.number for row in read_rows(path)] == ["1", "2"]

"""Story O12, criterion 5: the number check fails on every planted problem and passes on the seeded repository."""

from pathlib import Path

import pytest

from fno.numbering.categories import CATEGORIES
from fno.numbering.check import check_numbers
from fno.numbering.registry import read_rows
from fno.numbering.seed import seed_registries
from fno.numbering.seed_pin import seeded_digest, write_pins
from tests.numbering.helpers import HEADER, write

STAMP = "2026-10-16T10:00:00Z"
FILES = {
    "reviews/claude/response_1_a.md": "x\n",
    "reviews/claude/README.md": "index\n",
    "reviews/claude/a14_status.md": "not numbered\n",
    "reviews/chatgpt/review_1_a.md": "x\n",
    "reviews/judge/judge_1_a.md": "# Judge 1\n## Addendum 1\n## Addendum\n## Addendum 2 (16 Oct)\n",
}
CLEAN_REGISTRIES = {
    "numbers/claude-response.csv": HEADER + "1,response_1_a.md,existing,\n",
    "numbers/chatgpt-review.csv": HEADER + "1,review_1_a.md,existing,\n",
    "numbers/judge-report.csv": HEADER + f"1,judge_1_a.md,existing,\n2,judge_2_b.md,session_x,{STAMP}\n",
    "numbers/judge-addendum.csv": HEADER + f"1.1,judge_1_a.md,existing,\n1.2,round-2,session_x,{STAMP}\n",
}


def checkout(tmp_path: Path, category: str = "", registry: str = "") -> Path:
    """The clean checkout with its seed pinned, then one category's registry replaced when given."""
    pin(write(tmp_path, {**FILES, **CLEAN_REGISTRIES}))
    return write(tmp_path, {f"numbers/{category}.csv": registry} if category else {})


def pin(root: Path) -> Path:
    """Pins the seeded rows as they stand, as the seed does at the merge."""
    write_pins(root, {c.name: seeded_digest(read_rows(root / c.registry)) for c in CATEGORIES.values()})
    return root


def test_a_clean_checkout_passes_and_a_claim_without_its_file_yet_is_fine(tmp_path):
    assert check_numbers(checkout(tmp_path)) == []  # judge 2 is claimed, its file not written yet


def test_an_unregistered_file_or_heading_fails(tmp_path):
    root = checkout(tmp_path)
    write(root, {"reviews/claude/response_2_new.md": "x\n"})
    (root / "reviews/judge/judge_1_a.md").write_text(FILES["reviews/judge/judge_1_a.md"] + "## Addendum 3\n")
    assert check_numbers(root) == [
        "reviews/claude/response_2_new.md: number 2 has no row in numbers/claude-response.csv",
        "reviews/judge/judge_1_a.md: number 1.3 has no row in numbers/judge-addendum.csv",
    ]


def test_a_file_whose_name_differs_from_its_row_fails(tmp_path):
    root = checkout(tmp_path)
    (root / "reviews/claude/response_1_a.md").rename(root / "reviews/claude/response_1_renamed.md")
    assert check_numbers(root) == [
        "reviews/claude/response_1_renamed.md: number 1 has no row in numbers/claude-response.csv"
    ]


def test_a_number_taken_twice_after_the_seed_fails(tmp_path):
    root = checkout(tmp_path)
    write(root, {"reviews/judge/judge_2_b.md": "x\n", "reviews/judge/judge_2_c.md": "y\n"})
    with (root / "numbers/judge-report.csv").open("a") as registry:
        registry.write(f"2,judge_2_c.md,session_y,{STAMP}\n")
    assert check_numbers(root) == [
        "numbers/judge-report.csv: number 2 is used 2 times (judge_2_b.md, judge_2_c.md); "
        "only seeded history may repeat a number"
    ]


def test_two_headings_with_one_number_fail_unless_both_are_seeded(tmp_path):
    root = checkout(tmp_path)
    (root / "reviews/judge/judge_1_a.md").write_text(FILES["reviews/judge/judge_1_a.md"] + "## Addendum 2\n")
    assert check_numbers(root) == [
        "numbers/judge-addendum.csv: number 1.2 is used 2 times (judge_1_a.md, round-2); "
        "only seeded history may repeat a number"
    ]


def test_seeded_history_may_repeat_a_number(tmp_path):
    seeded = HEADER + "1,response_1_a.md,existing,\n1,response_1_b.md,existing,\n"
    root = pin(checkout(tmp_path, "claude-response", seeded))
    write(root, {"reviews/claude/response_1_b.md": "x\n"})
    assert check_numbers(root) == []


@pytest.mark.parametrize("where", ["first", "last"])
def test_a_seeded_row_added_after_the_pin_fails_wherever_it_sits(tmp_path, where):
    clash = "1,response_1_b.md,existing,\n"
    rows = "1,response_1_a.md,existing,\n" + f"9,response_9_x.md,session_x,{STAMP}\n"
    registry = HEADER + (clash + rows if where == "first" else rows + clash)
    root = checkout(tmp_path, "claude-response", registry)
    write(root, {"reviews/claude/response_1_b.md": "x\n"})
    assert check_numbers(root) == [
        "numbers/claude-response.csv: the seeded rows differ from their pin in fno/numbering/seed_pins.json; "
        "the seed is history only"
    ]


def test_a_misnamed_series_file_fails(tmp_path):
    root = checkout(tmp_path)
    write(root, {"reviews/claude/response_07_b.md": "x\n", "reviews/chatgpt/review_7.md": "x\n"})
    assert check_numbers(root) == [
        "reviews/claude/response_07_b.md: not a response_<n>_<slug>.md name, so its number cannot be checked",
        "reviews/chatgpt/review_7.md: not a review_<n>_<slug>.md name, so its number cannot be checked",
    ]


def test_a_level_3_heading_counts_and_a_quoted_one_in_a_code_block_does_not(tmp_path):
    root = checkout(tmp_path)
    text = FILES["reviews/judge/judge_1_a.md"] + "```\n## Addendum 1\n## Addendum 9\n```\n### Addendum 4\n"
    (root / "reviews/judge/judge_1_a.md").write_text(text)
    assert check_numbers(root) == ["reviews/judge/judge_1_a.md: number 1.4 has no row in numbers/judge-addendum.csv"]


def test_one_line_per_unregistered_heading_even_when_repeated(tmp_path):
    root = checkout(tmp_path)
    (root / "reviews/judge/judge_1_a.md").write_text(FILES["reviews/judge/judge_1_a.md"] + "## Addendum 5\n" * 2)
    assert check_numbers(root) == [
        "reviews/judge/judge_1_a.md: number 1.5 has no row in numbers/judge-addendum.csv",
        "numbers/judge-addendum.csv: number 1.5 is used 2 times (judge_1_a.md); "
        "only seeded history may repeat a number",
    ]


@pytest.mark.parametrize(
    ("row", "reason"),
    [
        (f"2.1,judge_2_b.md,s,{STAMP}", "number is not of this category's form"),
        (f"02,judge_2_b.md,s,{STAMP}", "number is not of this category's form"),
        (f"2,,s,{STAMP}", "no name"),
        (f"2,judge_2_b.md,,{STAMP}", "no claiming session"),
        ("2,judge_2_b.md,s,2026-10-16 10:00", "claimed_at_utc is not YYYY-MM-DDTHH:MM:SSZ"),
        ("2,judge_2_b.md,s,", "claimed_at_utc is not YYYY-MM-DDTHH:MM:SSZ"),
    ],
)
def test_a_malformed_row_fails(tmp_path, row, reason):
    root = checkout(tmp_path, "judge-report", HEADER + "1,judge_1_a.md,existing,\n" + row + "\n")
    number, name = row.split(",")[:2]
    assert check_numbers(root) == [f"numbers/judge-report.csv: row {number},{name}: {reason}"]


def test_a_seeded_row_with_a_time_fails(tmp_path):
    registry = HEADER + "1,judge_1_a.md,existing,\n" + f"2,judge_2_b.md,existing,{STAMP}\n"
    assert check_numbers(pin(checkout(tmp_path, "judge-report", registry))) == [
        "numbers/judge-report.csv: row 2,judge_2_b.md: a seeded row has no time"
    ]


def test_an_addendum_number_must_have_both_parts(tmp_path):
    root = checkout(
        tmp_path, "judge-addendum", HEADER + f"1.1,judge_1_a.md,existing,\n1.2,round-2,s,{STAMP}\n3,x,s,{STAMP}\n"
    )
    assert check_numbers(root) == ["numbers/judge-addendum.csv: row 3,x: number is not of this category's form"]


def test_a_broken_header_is_one_finding(tmp_path):
    root = checkout(tmp_path, "chatgpt-review", "number,name\n1,review_1_a.md\n")
    assert check_numbers(root) == [
        "numbers/chatgpt-review.csv: the first line must be number,name,session,claimed_at_utc"
    ]


def test_the_seed_registers_history_once_with_its_duplicates_and_pins_it(tmp_path):
    root = write(tmp_path, {**FILES, "reviews/claude/response_1_b.md": "x\n"})
    assert check_numbers(root) != []
    assert seed_registries(root) == 6  # 2 responses, 1 review, 1 report, 2 addenda
    pins = (root / "fno/numbering/seed_pins.json").read_text()
    assert seed_registries(root) == 0
    assert (root / "fno/numbering/seed_pins.json").read_text() == pins
    assert check_numbers(root) == []
    assert (root / "numbers/claude-response.csv").read_text() == (
        HEADER + "1,response_1_a.md,existing,\n1,response_1_b.md,existing,\n"
    )


def test_a_reservation_row_holds_its_number_and_registers_the_file_when_it_lands(tmp_path):
    reserved = f"3,response_3_*.md,session_orchestrator,{STAMP}\n"
    root = checkout(tmp_path, "claude-response", CLEAN_REGISTRIES["numbers/claude-response.csv"] + reserved)
    assert check_numbers(root) == []  # reserved, no file yet
    write(root, {"reviews/claude/response_3_o12.md": "x\n"})
    assert check_numbers(root) == []
    assert seed_registries(root) == 0  # the seed does not add it again as history
    write(root, {"reviews/claude/response_3_other.md": "y\n"})
    assert check_numbers(root)[-1].startswith("numbers/claude-response.csv: number 3 is used 2 times")


def test_a_claimed_row_reusing_a_number_seeded_once_fails(tmp_path):
    reused = f"1,response_1_c.md,session_y,{STAMP}\n"
    root = checkout(tmp_path, "claude-response", CLEAN_REGISTRIES["numbers/claude-response.csv"] + reused)
    assert check_numbers(root) == [
        "numbers/claude-response.csv: number 1 is used 2 times (response_1_a.md, response_1_c.md); "
        "only seeded history may repeat a number"
    ]

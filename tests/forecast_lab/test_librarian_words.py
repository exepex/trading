"""FL1-1d-2 (judge 438.1): the evening routine tells a file NSE has not published yet ("not out yet", no alert) from
any other librarian problem (posted to #fno-desk) by the librarian's own words. This pins those words: if A9's
librarian ever words them otherwise, this fails and the routine's CLAUDE.md step must change with it."""

from datetime import date

from fno.storage.librarian import FillReport, fill_report_lines
from fno.storage.librarian_cli import SOURCE_STOPPED

DAY = date(2026, 10, 21)
NOT_PUBLISHED = "not published by the source"
OTHER_PROBLEMS = ("damaged in store", "rejected from source", "stopped:")


def test_a_file_not_published_yet_has_its_own_words_and_no_other_problem_shares_them():
    report = FillReport("fo-bhavcopy", DAY, DAY, sessions=1, not_published=[DAY])
    lines = fill_report_lines(report)
    assert f"{NOT_PUBLISHED} {DAY}" in lines and lines[-1] == "result: INCOMPLETE: see the lines above"
    damaged = FillReport("fo-bhavcopy", DAY, DAY, sessions=1, damaged=[(DAY, "bad zip")],
                         rejected=[(DAY, "no rows")])  # fmt: skip
    problems = fill_report_lines(damaged)
    assert any(line.startswith(OTHER_PROBLEMS[0]) for line in problems)
    assert any(line.startswith(OTHER_PROBLEMS[1]) for line in problems)
    assert not any(NOT_PUBLISHED in line for line in problems)
    assert SOURCE_STOPPED.startswith(OTHER_PROBLEMS[2])

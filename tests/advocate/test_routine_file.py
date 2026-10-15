"""The objecting AI behind the advocate port (LR1, reused by T3): the routine's objections file and its checks."""

import hashlib

import pytest

from fno.advocate.port import AdvocateResult, AdvocateSubject
from fno.advocate.routine_file import RoutineFileAdvocate, objections_path

LINES = "Header 2026-10-17\nweather_vix_v1: scored 40%\nComplete days: 3 of 5\n"


def _subject(tmp_path, objections: str | None) -> AdvocateSubject:
    lines = tmp_path / "2026-10-17.md"
    lines.write_text(LINES)
    sha = hashlib.sha256(lines.read_bytes()).hexdigest()
    if objections is not None:
        objections_path(lines).write_text(objections.replace("SHA", sha))
    return AdvocateSubject("weekly post-mortem 2026-10-17", lines, sha)


def test_checked_objections_are_returned(tmp_path):
    text = "SHA\n[L2] 40% rests on back-fill rows, not live ones.\n[L3] 3 of 5 days is too few to judge."
    result = RoutineFileAdvocate().objections(_subject(tmp_path, text))
    assert result.ran and len(result.objections) == 2 and result.lines()[0].startswith("[L2]")


def test_no_file_is_not_run(tmp_path):
    assert RoutineFileAdvocate().objections(_subject(tmp_path, None)) == AdvocateResult(
        not_run="no objections received"
    )


@pytest.mark.parametrize(
    ("text", "reason"),
    [
        ("b" * 64 + "\n[L2] fine.", "rule 1"),
        ("SHA\n", "rule 2: 0 objections"),
        ("SHA\n" + "\n".join(f"[L2] point {chr(97 + i)}." for i in range(6)), "rule 2: 6 objections"),
        ("SHA\n[L2] " + "word " * 41, "rule 2: more than 40 words"),
        ("SHA\n[L99] no such line.", "rule 2: objection 1 does not start"),
        ("SHA\nno line number here.", "rule 2: objection 1 does not start"),
        ("SHA\n[L2] see https://x.org", "rule 2: a link"),
        ("SHA\n[L2] 41% is not what it says.", "rule 3: number 41%"),
        ("SHA\n[L3] it happened twice.", "rule 4"),
    ],
)
def test_each_failed_rule_means_not_run(tmp_path, text, reason):
    result = RoutineFileAdvocate().objections(_subject(tmp_path, text))
    assert not result.ran and result.not_run.startswith(reason)
    assert result.lines() == [f"advocate not run: {result.not_run}"]

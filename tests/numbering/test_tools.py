"""Story O12: the two command lines print one plain result line and exit 1 when nothing was claimed or a check fails."""

from fno.numbering.claim import Claim, ClaimNotPushed, ClaimRefused
from tests.numbering.helpers import HEADER, write
from tools import check_numbers, claim_number


class Claimer:
    def __init__(self, result):
        self.result, self.requests = result, []

    def claim(self, request):
        self.requests.append(request)
        if isinstance(self.result, Exception):
            raise self.result
        return self.result


def test_a_claim_prints_the_number_and_the_file_to_write(capsys):
    claimer = Claimer(Claim("judge-addendum", "270.2", "round-2"))
    args = ["judge-addendum", "round-2", "--session", "session_a", "--report", "270"]
    assert claim_number.main(args, claimer) == 0
    assert capsys.readouterr().out == "claimed: judge-addendum 270.2 -> round-2\n"
    sent = claimer.requests[0]
    assert (sent.category.name, sent.slug, sent.session, sent.report, sent.exact) == (
        "judge-addendum",
        "round-2",
        "session_a",
        "270",
        None,
    )


def test_a_refused_or_lost_claim_exits_1(capsys):
    for failure in (ClaimRefused("judge-report 66 is already claimed"), ClaimNotPushed("8 pushes refused")):
        assert claim_number.main(["judge-report", "x", "--session", "s", "--number", "66"], Claimer(failure)) == 1
    assert capsys.readouterr().out.splitlines() == [
        "number claim: NOT claimed (judge-report 66 is already claimed)",
        "number claim: NOT claimed (8 pushes refused)",
    ]


def test_the_check_prints_each_problem_and_exits_1(tmp_path, capsys):
    write(tmp_path, {"reviews/claude/response_1_a.md": "x\n"})
    assert check_numbers.main(["--root", str(tmp_path)]) == 1
    assert capsys.readouterr().out.splitlines()[-2:] == [
        "reviews/claude/response_1_a.md: number 1 has no row in numbers/claude-response.csv",
        "number check: FAILED, 1 problem(s); claim numbers with tools/claim_number.py (docs/stories/O12)",
    ]
    assert check_numbers.main(["--root", str(tmp_path), "--seed"]) == 0
    assert capsys.readouterr().out.splitlines() == ["number seed: 1 row(s) added", "number check: clean"]
    assert (tmp_path / "numbers/claude-response.csv").read_text() == HEADER + "1,response_1_a.md,existing,\n"

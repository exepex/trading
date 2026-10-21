"""Story O12: the two command lines print one plain result line and exit 1 when nothing was claimed or a check fails."""

from pathlib import Path

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
    assert capsys.readouterr().out == (
        "claimed: judge-addendum 270.2 -> round-2\n"
        "next: write the heading '## Addendum 2' in reviews/judge/judge_270_*.md\n"
    )
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


class Alerts:
    def __init__(self):
        self.sent = []

    def send(self, text):
        self.sent.append(text)
        return "alert sent"


def test_alert_posts_the_problem_lines_and_nothing_when_clean(tmp_path, capsys):
    write(tmp_path, {"reviews/claude/response_1_a.md": "x\n"})
    alerts = Alerts()
    assert check_numbers.main(["--root", str(tmp_path), "--alert"], alerts) == 1
    assert alerts.sent == [
        "Omenix F&O number check is red on main: 1 new problem(s). Register the file's number in numbers/ or rename "
        "it (numbers/README.md); the check names the file and line:\n"
        "reviews/claude/response_1_a.md: number 1 has no row in numbers/claude-response.csv"
    ]
    assert capsys.readouterr().out.splitlines()[-1] == "alert sent"
    clean = write(tmp_path / "clean", {"reviews/claude/README.md": "index\n"})
    assert check_numbers.main(["--root", str(clean), "--alert"], alerts) == 0
    assert len(alerts.sent) == 1


def test_with_a_baseline_only_new_problems_are_posted(tmp_path):
    before = write(tmp_path / "before", {"reviews/claude/response_1_a.md": "x\n"})
    after = write(tmp_path / "after", {"reviews/claude/response_1_a.md": "x\n"})
    alerts = Alerts()
    assert check_numbers.main(["--root", str(after), "--alert", "--baseline", str(before)], alerts) == 1
    assert alerts.sent == []  # already red before this push: announced then
    write(after, {"reviews/judge/judge_2_b.md": "x\n"})
    assert check_numbers.main(["--root", str(after), "--alert", "--baseline", str(before)], alerts) == 1
    assert len(alerts.sent) == 1
    assert alerts.sent[0].endswith("reviews/judge/judge_2_b.md: number 2 has no row in numbers/judge-report.csv")
    assert "1 new problem(s)" in alerts.sent[0] and "response_1_a" not in alerts.sent[0]


def test_the_alert_workflow_runs_on_every_push_and_hourly_with_the_push_baseline():
    steps = (Path(__file__).resolve().parents[2] / ".github" / "workflows" / "number-alert.yml").read_text()
    assert '  push:\n    branches: [main]\n  schedule:\n    - cron: "17 * * * *"' in steps
    assert "run: python tools/check_numbers.py --alert ${{ steps.baseline.outputs.args }}" in steps
    assert "FNO_SLACK_BOT_TOKEN: ${{ secrets.FNO_SLACK_BOT_TOKEN }}" in steps


def test_a_file_claim_names_the_file_to_write(capsys):
    claimer = Claimer(Claim("claude-response", "283", "response_283_x.md"))
    assert claim_number.main(["claude-response", "x", "--session", "s"], claimer) == 0
    assert capsys.readouterr().out.splitlines() == [
        "claimed: claude-response 283 -> response_283_x.md",
        "next: write reviews/claude/response_283_x.md",
    ]

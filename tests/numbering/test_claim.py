"""Story O12, criteria 2-4: a claim is one registry row pushed to `main`; a race is won by exactly one push."""

import time
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime

import pytest

from fno.numbering.categories import CLAUDE_RESPONSE, JUDGE_ADDENDUM, JUDGE_REPORT
from fno.numbering.claim import Claim, ClaimNotPushed, ClaimRefused, ClaimRequest, NumberClaimer
from fno.numbering.git_main import GitFailed, GitMain
from tests.numbering.helpers import HEADER, git, origin_and_clones, origin_file
from tools import claim_number

NOW = datetime(2026, 10, 16, 10, 0, 0, tzinfo=UTC)
MAIN = {
    "numbers/claude-response.csv": HEADER + "1,response_1_a.md,existing,\n",
    "numbers/judge-report.csv": HEADER + "270,judge_270_a.md,existing,\n",
    "numbers/judge-addendum.csv": HEADER + "270.1,judge_270_a.md,existing,\n",
    "reviews/claude/response_1_a.md": "x\n",
}


def claimer(clone, pauses=None, tries=8, git_main=None):
    pauses = [] if pauses is None else pauses
    return NumberClaimer(git_main or GitMain(clone), clock=lambda: NOW, pause=pauses.append, tries=tries)


def request(category=CLAUDE_RESPONSE, slug="new-work", session="session_a", **extra):
    return ClaimRequest(category, slug, session, **extra)


def test_a_claim_pushes_one_row_and_leaves_the_callers_checkout_alone(tmp_path):
    clone, _ = origin_and_clones(tmp_path, MAIN)
    git(clone, "checkout", "-q", "-b", "story/x")
    (clone / "work.txt").write_text("unsaved\n")
    git(clone, "add", "work.txt")
    assert claimer(clone).claim(request()) == Claim("claude-response", "2", "response_2_new-work.md")
    assert origin_file(tmp_path, "numbers/claude-response.csv").endswith(
        "2,response_2_new-work.md,session_a,2026-10-16T10:00:00Z"
    )
    assert git(tmp_path / "origin.git", "show", "--stat", "--format=%s", "main").splitlines()[:2] == [
        "Number claim: claude-response 2 response_2_new-work.md",
        "",
    ]
    assert git(tmp_path / "origin.git", "diff", "--name-only", "main~1", "main") == "numbers/claude-response.csv"
    assert git(clone, "branch", "--show-current") == "story/x"
    assert git(clone, "status", "--porcelain") == "A  work.txt"
    assert len(git(clone, "worktree", "list").splitlines()) == 1


def test_two_racing_claims_both_win_with_different_numbers(tmp_path):
    clone_a, clone_b = origin_and_clones(tmp_path, MAIN)
    other_first = RivalFirst(GitMain(clone_a), lambda: claimer(clone_b).claim(request(session="session_b")))
    pauses = []
    assert claimer(clone_a, pauses, git_main=other_first).claim(request(slug="mine")).number == "3"
    rows = origin_file(tmp_path, "numbers/claude-response.csv").splitlines()[2:]
    assert [row.split(",")[:3] for row in rows] == [
        ["2", "response_2_new-work.md", "session_b"],
        ["3", "response_3_mine.md", "session_a"],
    ]
    assert len(pauses) == 1 and 0.5 <= pauses[0] <= 3.0


def test_four_sessions_claiming_at_once_get_four_different_numbers(tmp_path):
    clones = origin_and_clones(tmp_path, MAIN, clones=4)
    claimers = [NumberClaimer(GitMain(c), clock=lambda: NOW, pause=lambda s: time.sleep(s / 20)) for c in clones]
    with ThreadPoolExecutor(4) as pool:
        claims = list(pool.map(lambda n: claimers[n].claim(request(slug=f"s{n}", session=f"session_{n}")), range(4)))
    assert sorted(int(c.number) for c in claims) == [2, 3, 4, 5]
    rows = origin_file(tmp_path, "numbers/claude-response.csv").splitlines()[2:]
    assert sorted(row.split(",")[0] for row in rows) == ["2", "3", "4", "5"]


def test_when_every_push_is_refused_nothing_is_claimed(tmp_path):
    clone, _ = origin_and_clones(tmp_path, MAIN)
    pauses = []
    with pytest.raises(ClaimNotPushed, match="3 pushes to main were refused"):
        claimer(clone, pauses, tries=3, git_main=NeverPushes(GitMain(clone))).claim(request())
    assert len(pauses) == 2  # no pause after the last try
    assert origin_file(tmp_path, "numbers/claude-response.csv") == MAIN["numbers/claude-response.csv"].strip()
    assert len(git(clone, "worktree", "list").splitlines()) == 1


def test_an_exact_number_is_claimed_when_free_and_refused_when_taken(tmp_path):
    clone, _ = origin_and_clones(tmp_path, MAIN)
    assert claimer(clone).claim(request(JUDGE_REPORT, exact="66")).name == "judge_66_new-work.md"
    with pytest.raises(ClaimRefused, match="judge-report 66 is already taken"):
        claimer(clone).claim(request(JUDGE_REPORT, exact="66"))
    assert claimer(clone).claim(request(JUDGE_REPORT)).number == "271"  # after the highest, not after 66


def test_a_file_on_main_without_a_row_is_never_handed_out_again(tmp_path):
    files = {**MAIN, "reviews/claude/response_5_old-habit.md": "x\n", "reviews/judge/judge_270_a.md": "## Addendum 4\n"}
    clone, _ = origin_and_clones(tmp_path, files)
    assert claimer(clone).claim(request()).number == "6"
    with pytest.raises(ClaimRefused, match="claude-response 5 is already taken"):
        claimer(clone).claim(request(exact="5"))
    assert claimer(clone).claim(request(JUDGE_ADDENDUM, report="270")).number == "270.5"


def test_a_push_refused_for_another_reason_stops_at_once_with_gits_words(tmp_path):
    clone, _ = origin_and_clones(tmp_path, MAIN)
    hook = tmp_path / "origin.git" / "hooks" / "pre-receive"
    hook.write_text("#!/bin/sh\necho 'access denied for this key' >&2\nexit 1\n")
    hook.chmod(0o755)
    pauses = []
    with pytest.raises(GitFailed, match="access denied for this key"):
        claimer(clone, pauses).claim(request())
    assert pauses == []
    assert len(git(clone, "worktree", "list").splitlines()) == 1


def test_addenda_are_numbered_per_report_and_need_the_report(tmp_path):
    clone, _ = origin_and_clones(tmp_path, MAIN)
    assert claimer(clone).claim(request(JUDGE_ADDENDUM, "round-2", report="270")) == Claim(
        "judge-addendum", "270.2", "round-2"
    )
    with pytest.raises(ClaimRefused, match="report 271 is not on main"):
        claimer(clone).claim(request(JUDGE_ADDENDUM, report="271"))


@pytest.mark.parametrize(
    ("bad", "message"),
    [
        (request(slug="Bad Slug"), "slug 'Bad Slug'"),
        (request(slug=""), "slug ''"),
        (request(slug="a--b"), "slug 'a--b'"),
        (request(session=" "), "name the claiming session"),
        (request(session="existing"), "'existing' is reserved"),
        (request(JUDGE_ADDENDUM), "--report is required"),
        (request(report="270"), "--report is not allowed"),
        (request(exact="0"), "--number '0'"),
        (request(exact="07"), "--number '07'"),
        (request(exact="x"), "--number 'x'"),
    ],
)
def test_a_wrong_request_is_refused_before_touching_git(tmp_path, bad, message):
    with pytest.raises(ClaimRefused, match=message):
        claimer(tmp_path / "not-a-repository").claim(bad)


def test_no_remote_stops_with_a_git_failure(tmp_path):
    git(tmp_path, "init", "-q")
    with pytest.raises(GitFailed, match="git fetch"):
        claimer(tmp_path).claim(request())


class RivalFirst:
    """Lets a rival claim land on `main` just before this claimant's first push."""

    def __init__(self, inner, rival):
        self._inner, self._rival = inner, rival

    def main_copy(self):
        return _Wrapped(self._inner.main_copy(), self._before_push)

    def _before_push(self):
        rival, self._rival = self._rival, None
        if rival:
            rival()


class NeverPushes(RivalFirst):
    def __init__(self, inner):
        super().__init__(inner, None)

    def main_copy(self):
        return _Wrapped(self._inner.main_copy(), None, refuse=True)


class _Wrapped:
    def __init__(self, context, before_push, refuse=False):
        self._context, self._before_push, self._refuse = context, before_push, refuse

    def __enter__(self):
        copy = self._context.__enter__()
        push = copy.commit_and_push

        def commit_and_push(registry, message):
            if self._before_push:
                self._before_push()
            return False if self._refuse else push(registry, message)

        copy.commit_and_push = commit_and_push
        return copy

    def __exit__(self, *exc):
        return self._context.__exit__(*exc)


def test_a_reserved_number_is_taken(tmp_path):
    reserved = {**MAIN, "numbers/claude-response.csv": MAIN["numbers/claude-response.csv"] + "9,response_9_*.md,o,t\n"}
    clone, _ = origin_and_clones(tmp_path, reserved)
    assert claimer(clone).claim(request()).number == "10"
    with pytest.raises(ClaimRefused, match="claude-response 9 is already taken"):
        claimer(clone).claim(request(exact="9"))


@pytest.mark.parametrize(
    ("hook", "printed"),
    [
        # a crashing hook, as when this Python lacks a package (judge B, 22 Oct: xlrd)
        ("echo 'Traceback: ImportError: No module named xlrd' >&2; exit 1", "No module named xlrd"),
        # the record scan refusing: its findings are on stdout, which must not be lost
        ("echo 'numbers/x.csv:2: AWS access key'; echo 'record scan: REFUSED, 1 finding(s)'; exit 1", "REFUSED"),
    ],
)
def test_a_refused_commit_stops_loudly_with_the_hooks_own_words_and_pushes_nothing(tmp_path, capsys, hook, printed):
    clone, _ = origin_and_clones(tmp_path, MAIN)
    hooks = tmp_path / "hooks"
    hooks.mkdir()
    (hooks / "pre-commit").write_text(f"#!/bin/sh\n{hook}\n")
    (hooks / "pre-commit").chmod(0o755)
    git(clone, "config", "core.hooksPath", str(hooks))
    with pytest.raises(GitFailed) as failed:
        claimer(clone).claim(request())
    assert failed.value.step == "commit" and printed in failed.value.output
    assert origin_file(tmp_path, "numbers/claude-response.csv") == MAIN["numbers/claude-response.csv"].strip()
    assert len(git(clone, "worktree", "list").splitlines()) == 1
    assert claim_number.main(["claude-response", "x", "--session", "s", "--root", str(clone)]) == 1
    out = capsys.readouterr().out.strip().splitlines()
    assert printed in "\n".join(out[:-1])  # the hook's own words first
    assert out[-1].startswith("number claim: NOT claimed (the commit was refused, by the record-scan hook")
    assert out[-1].endswith("Nothing was pushed: do not write the file; fix it and claim again.")

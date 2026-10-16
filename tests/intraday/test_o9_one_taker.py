"""Story O9 section 6 (step 2a): one taker per mark, failed quotes retried once with Groww's code kept, and an alert
that says the realised variance is safe when only contract quotes are missing."""

import json
import subprocess
from datetime import date, datetime, time

from fno.intraday.claims import LOST, UNCLAIMED, WON, ClaimResult, GitMarkClaims, MarkClaims, NoClaims
from fno.intraday.groww_source import failure_name
from fno.intraday.recorder import ALREADY
from fno.intraday.streak import EFFECT_QUOTES, EFFECT_VOID, streak_alert_text
from fno.storage.manifest_commit import GitManifestRecorder
from fno.storage.owned_paths_commit import OwnedPathsCommitter
from tests.intraday.fakes import DAY, FakeClock, build, ist
from tests.intraday.groww_fakes import FakeGrowwApi
from tests.intraday.test_groww_source import source

CLAIMS = "receipts/intraday/claims"


class FailsOnce(FakeGrowwApi):
    """A quote that fails on its first call only, like 16 Oct's lone 429 at 11:15."""

    def __init__(self, symbol: str):
        super().__init__()
        self.symbol = symbol

    def get_quote(self, trading_symbol, exchange, segment, timeout=None):
        if trading_symbol == self.symbol and f"quote {trading_symbol}" not in self.calls:
            self.calls.append(f"quote {trading_symbol}")
            raise RuntimeError("Bad Request")
        return super().get_quote(trading_symbol, exchange, segment, timeout)


def test_a_quote_that_failed_once_is_asked_again_and_kept():
    symbol = "NIFTY26101925000CE"
    api = FailsOnce(symbol)
    found = source(api).take(DAY, ist(DAY, 10, 0))
    assert not [q for q in found.quotes if q.failure] and found.recorded_contracts == found.expected_contracts
    assert api.calls.count(f"quote {symbol}") == 2 and "quotes_retried:1" in found.notes


def test_a_quote_that_fails_again_is_kept_as_failed_after_one_retry():
    symbol = "NIFTY26101925000CE"
    api = FakeGrowwApi(fail=(symbol,))
    found = source(api).take(DAY, ist(DAY, 10, 0))
    assert [q.failure for q in found.quotes if q.failure] == ["RuntimeError"]
    assert api.calls.count(f"quote {symbol}") == 2  # one retry, never a loop


class CodedError(Exception):
    def __init__(self, code):
        super().__init__("Rate limit has breached for your request. Please try again later.")
        self.code = code


def test_groww_code_is_kept_with_the_class_and_never_the_message():
    assert failure_name(CodedError("429")) == "CodedError:429"
    assert failure_name(CodedError("not a short code at all")) == "CodedError"
    assert failure_name(RuntimeError("x")) == "RuntimeError"


def rows(*statuses):
    return [{"mark": f"2026-10-16T0{3 + i}:00:00+00:00", "mark_ist": f"1{i}:00", "status": s, "failures": "x",
             "session": "2026-10-16", "alert": "", "alert_at": ""} for i, s in enumerate(statuses)]  # fmt: skip


def test_an_alert_on_incomplete_marks_says_the_realised_variance_is_not_affected():
    text = streak_alert_text(rows("incomplete", "incomplete"), datetime(2026, 10, 16, 12))
    assert EFFECT_QUOTES in text and "two runs taking one mark" in text and EFFECT_VOID not in text


def test_an_alert_with_a_missed_mark_says_the_realised_variance_will_be_void():
    text = streak_alert_text(rows("incomplete", "missed"), datetime(2026, 10, 16, 12))
    assert EFFECT_VOID in text and "does Groww sign in" in text


class LosesFirstMark(MarkClaims):
    def __init__(self, clock):
        self.clock, self.asked = clock, []

    def claim(self, day: date, mark: datetime) -> ClaimResult:
        self.asked.append((mark, self.clock.now()))
        return ClaimResult(LOST, "other-run") if mark == ist(DAY, 9, 15) else ClaimResult(WON, "me")


def test_a_run_that_loses_a_mark_takes_none_of_it_and_takes_the_next(tmp_path):
    clock = FakeClock(ist(DAY, 9, 5))
    recorder, source_, *_ = build(tmp_path, clock)
    recorder.claims = claims = LosesFirstMark(clock)
    outcomes = recorder.run(time(9, 35))
    assert [f"{m:%H:%M}" for m in source_.taken] == ["09:30"]
    assert outcomes[0].status == ALREADY and "other-run" in outcomes[0].detail
    assert claims.asked[0][1] == ist(DAY, 9, 14, 15)  # claimed 45 s before the mark, not when it began waiting


def git(folder, *args):
    return subprocess.run(["git", *args], cwd=folder, check=True, capture_output=True, text=True).stdout


def clone(tmp_path, origin, name):
    folder = tmp_path / name
    git(tmp_path, "clone", "-q", str(origin), str(folder))
    for key, value in (("user.name", name), ("user.email", "t@example.invalid"), ("core.hooksPath", "hooks")):
        git(folder, "config", key, value)
    return folder


def claims_in(folder, run_id):
    committer = GitManifestRecorder(folder, folder / CLAIMS, message="Claim ({what})", label="claim",
                                    keep_remote_on_conflict=True)  # fmt: skip
    return GitMarkClaims(folder / CLAIMS, committer, run_id, lambda: datetime(2026, 10, 16, 9, 14, 15))


def origin_with_two_clones(tmp_path):
    origin = tmp_path / "origin.git"
    git(tmp_path, "init", "-q", "--bare", "-b", "main", str(origin))
    first = clone(tmp_path, origin, "a")
    (first / "README.md").write_text("x\n")
    git(first, "add", "README.md")
    git(first, "commit", "-q", "-m", "start")
    git(first, "push", "-q", "origin", "HEAD:main")
    return origin, first, clone(tmp_path, origin, "b")


def test_two_runs_racing_for_one_mark_exactly_one_wins_and_the_loser_keeps_the_winners_claim(tmp_path):
    origin, a, b = origin_with_two_clones(tmp_path)
    mark = ist(DAY, 9, 15)
    first = claims_in(a, "run-a").claim(DAY, mark)
    second = claims_in(b, "run-b").claim(DAY, mark)  # b had not seen a's claim: an add/add conflict on pull
    assert (first.outcome, second.outcome, second.holder) == (WON, LOST, "run-a")
    on_main = git(origin, "show", f"main:{CLAIMS}/{DAY:%Y-%m-%d}/0915.json")
    assert json.loads(on_main)["run_id"] == "run-a"
    assert json.loads((b / CLAIMS / f"{DAY:%Y-%m-%d}" / "0915.json").read_text())["run_id"] == "run-a"
    assert claims_in(a, "run-a").claim(DAY, mark).outcome == WON  # asking again changes nothing
    assert claims_in(b, "run-b").claim(DAY, ist(DAY, 9, 30)).outcome == WON  # the next mark is b's to take


def test_a_run_that_cannot_reach_github_takes_the_mark_anyway(tmp_path):
    origin, a, _ = origin_with_two_clones(tmp_path)
    git(a, "remote", "set-url", "origin", str(tmp_path / "missing.git"))
    result = claims_in(a, "run-a").claim(DAY, ist(DAY, 9, 15))
    assert result.outcome == UNCLAIMED and result.take and "NOT committed" in result.detail


INTRADAY = "research/data/intraday"


def run_committers(folder, run_id, shared=True):
    """The claims committer and the ledger committer of one recorder run in one checkout (judge 247)."""
    claims_paths, ledger_paths = (f"{CLAIMS}/",), (f"{INTRADAY}/slots/",)
    claims = GitManifestRecorder(folder, folder / CLAIMS, message="Claim ({what})", label="claim",
                                 keep_remote_on_conflict=True, run_paths=ledger_paths if shared else ())  # fmt: skip
    ledger = OwnedPathsCommitter(folder, folder / INTRADAY, ("slots/",), label="intraday slots",
                                 keep_remote_on_conflict=True, run_paths=claims_paths if shared else ())  # fmt: skip
    return GitMarkClaims(folder / CLAIMS, claims, run_id, lambda: datetime(2026, 10, 16, 9, 14, 15)), ledger


def test_a_claim_lost_to_a_network_blip_never_blocks_the_runs_later_pushes(tmp_path):
    origin, a, _ = origin_with_two_clones(tmp_path)
    claims, ledger = run_committers(a, "run-a")
    git(a, "remote", "set-url", "origin", str(tmp_path / "missing.git"))
    assert claims.claim(DAY, ist(DAY, 9, 15)).outcome == UNCLAIMED  # its commit stays local
    git(a, "remote", "set-url", "origin", str(origin))
    (a / INTRADAY / "slots").mkdir(parents=True)
    (a / INTRADAY / "slots" / "row_0915.csv").write_text("mark,status\n09:15,good\n")
    assert ledger.commit("09:15").startswith("intraday slots committed and pushed")
    assert claims.claim(DAY, ist(DAY, 9, 30)).outcome == WON
    on_main = git(origin, "ls-tree", "-r", "--name-only", "main").split()
    day = f"{DAY:%Y-%m-%d}"
    assert {f"{CLAIMS}/{day}/0915.json", f"{CLAIMS}/{day}/0930.json", f"{INTRADAY}/slots/row_0915.csv"} <= set(on_main)


def test_a_committer_still_refuses_changes_that_are_not_the_runs(tmp_path):
    origin, a, _ = origin_with_two_clones(tmp_path)
    claims, _ = run_committers(a, "run-a")
    (a / "code.py").write_text("unjudged\n")
    git(a, "add", "code.py")
    git(a, "commit", "-q", "-m", "unjudged code")
    result = claims.claim(DAY, ist(DAY, 9, 15))
    assert result.outcome == UNCLAIMED and "code.py" in result.detail
    assert "code.py" not in git(origin, "ls-tree", "-r", "--name-only", "main")


def test_a_lost_mark_is_never_asked_for_again(tmp_path):
    clock = FakeClock(ist(DAY, 9, 5))
    recorder, *_ = build(tmp_path, clock)
    recorder.claims = claims = LosesFirstMark(clock)
    recorder.run(time(9, 35))
    assert [f"{mark:%H:%M}" for mark, _ in claims.asked] == ["09:15", "09:30"]


def test_a_dry_run_claims_nothing_and_a_live_run_shares_its_paths_with_the_ledger(tmp_path):
    from fno.intraday import wiring

    assert isinstance(wiring._claims(tmp_path), NoClaims)
    live = wiring._claims(None)
    assert isinstance(live, GitMarkClaims) and live.committer.run_paths == wiring._ledger_paths()
    assert "research/data/intraday/slots/" in live.committer.run_paths

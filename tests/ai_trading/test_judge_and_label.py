"""Story F1t criterion 16 (the judge, F4's port; `NoJudge` until F4 lands) and criterion 17b (the strategy label, the
owner's 25 Oct decision to let the AI books trade on paper before a strategy has passed)."""

import json

import pytest

from fno.ai_trading.no_judge import NOT_BUILT, NoJudge, VerdictRefused
from fno.ai_trading.outcome import JUDGE_FAILED, PROMOTED, REFUSED
from fno.ai_trading.ports import JudgeCase

from .builders import DAY, FakeDecider, FakeJudge, draft
from .day import BOOKS, DEADLINES, Day

CHOSEN = {"action": "trade", "outcome": "chosen", "reason": "IV rich"}


def chosen(day, status="research"):
    return {"decision": CHOSEN, "served": {"ai_decision_version": "", "strategy_status": status}}


def collected(tmp_path, judge=None, decider_changes=None, late=()):
    day = Day(tmp_path, judge=judge)
    if decider_changes is not None:
        day.deciders = {b: VersionedDecider(day.root, decider_changes) for b in BOOKS}
    day.fire()
    for book in (b for b in BOOKS if b not in late):
        day.seal(book, draft())
    day.observe(DEADLINES.receipt)
    for book in late:  # pushed after the receipt deadline's reading
        day.seal(book, draft(), when=(15, 10, 5))
    for book in BOOKS:
        day.reveal(book)
    day.observe(DEADLINES.reveal)
    return day, day.collect()


class VersionedDecider(FakeDecider):
    """A decider whose records carry the accepted version in `served` beside the given changes."""

    def decide(self, accepted):
        changes = dict(self.changes)
        if "served" in changes:
            changes["served"] = {**changes["served"], "ai_decision_version": accepted.version}
        self.changes = changes
        return super().decide(accepted)


def status_of(result, book):
    return result.outcomes[book]["status"]


def test_a_passing_verdict_promotes_and_every_record_names_the_verdict_file(tmp_path):
    day, result = collected(tmp_path)
    accepted = day.deciders["book2_hybrid"].calls[0]
    assert status_of(result, "book2_hybrid") == PROMOTED and accepted.judge.endswith("_book2_hybrid_judge.json")
    assert accepted.judge_blocks is False and (day.root / accepted.judge).is_file()


def test_a_blocking_book2_verdict_is_judge_failed_with_its_no_trade_run_committed(tmp_path):
    day, result = collected(tmp_path, judge=FakeJudge(tmp_path / "repo", "fail", blocks=True))
    record = result.outcomes["book2_hybrid"]
    assert record["status"] == JUDGE_FAILED and "fail: test verdict fail" in record["reason"] and record["run_id"]
    assert day.deciders["book2_hybrid"].calls[0].judge_blocks is True  # decide() still ran, told of the block


def test_a_chosen_trade_under_a_blocking_verdict_is_refused_by_the_run_check(tmp_path):
    _, result = collected(tmp_path, judge=FakeJudge(tmp_path / "repo", "fail", blocks=True),
                          decider_changes=chosen(None))  # fmt: skip
    record = result.outcomes["book2_hybrid"]
    assert record["status"] == REFUSED and "blocking judge verdict" in record["reason"] and not record["run_id"]


def test_a_book_day_that_ends_before_the_judge_calls_no_judge(tmp_path):
    judge = FakeJudge(tmp_path / "repo")
    _, result = collected(tmp_path, judge=judge, late=("book3_ai",))
    assert status_of(result, "book3_ai") == "late" and [c.book for c in judge.cases] == ["book2_hybrid"]


def test_no_judge_fails_book2_closed_and_leaves_book3_free(tmp_path):
    day, result = collected(tmp_path, judge=NoJudge(tmp_path / "repo"))
    assert status_of(result, "book2_hybrid") == JUDGE_FAILED and NOT_BUILT in result.outcomes["book2_hybrid"]["reason"]
    assert status_of(result, "book3_ai") == PROMOTED
    verdict = json.loads((day.root / day.deciders["book3_ai"].calls[0].judge).read_text())
    assert (verdict["status"], verdict["blocks"], verdict["judge"]) == ("unavailable", False, "none:not-built")


def test_no_judge_writes_its_verdict_once(tmp_path):
    case = JudgeCase("book2_hybrid", DAY, "m", {"action": "trade", "reason": "r"}, {}, {}, "a" * 64, "b" * 64)
    judge = NoJudge(tmp_path)
    assert judge.run(case).path == judge.run(case).path  # the same bytes again: accepted
    with pytest.raises(VerdictRefused):
        judge.run(JudgeCase(**{**case.__dict__, "decision": {"action": "no_trade", "reason": "r"}}))


@pytest.mark.parametrize(("status", "label"), [("research", "strategy not yet passed"), ("paper", "strategy passed")])
def test_a_promoted_trade_carries_its_strategy_label(tmp_path, status, label):
    _, result = collected(tmp_path, decider_changes=chosen(None, status))
    assert (status_of(result, "book2_hybrid"), result.outcomes["book2_hybrid"]["strategy_label"]) == (PROMOTED, label)


def test_a_chosen_trade_without_its_strategy_status_is_refused_and_no_trade_has_no_label(tmp_path):
    _, result = collected(tmp_path, decider_changes={"decision": CHOSEN})
    assert (
        status_of(result, "book2_hybrid") == REFUSED and "strategy_status" in result.outcomes["book2_hybrid"]["reason"]
    )
    _, plain = collected(tmp_path / "plain")
    assert plain.outcomes["book2_hybrid"]["strategy_label"] == ""

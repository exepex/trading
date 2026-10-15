"""Judge 118 addendum 2, should-fix 1, at the daily run: a raw quote file staged earlier refuses the account write
before anything is applied, with the real `GitAccountSync` check. The fill step records "not filled" with an alert,
the journal is untouched, the other book fills and the run still reaches its exit review. The committer is a fake here,
so this is a file staged after the run's last commit (by another writer); one staged before a commit stops the run
(`test_commit_failure_run.py`)."""

import subprocess

from fno.books.account import PaperAccount
from fno.constants import BOOK1_RULES, BOOK2_HYBRID, OUTCOME_OPENED
from fno.desk.git_sync import Git, GitAccountSync

from .fakes import C4, Decisions, LocalSync, Rules, daily_run
from .test_daily_run import BOOKS, NORMAL, decided, run_day

RAW_QUOTE = "research/data/quotes/groww/derivatives/quote-snapshots/2026/10/nifty_20261014_151500.csv"


class StagedRawQuoteSync(LocalSync):
    """Book 1's writes go through the real check of a checkout whose index holds a raw quote file."""

    def __init__(self, root, checkout, alerts):
        super().__init__(root)
        self.real = GitAccountSync(Git(checkout), None, alerts)

    def write(self, book, apply, message):
        if book == BOOK1_RULES:
            self.real._require_no_raw_quote_staged(book)
        return super().write(book, apply, message)


def staged_checkout(tmp_path):
    checkout = tmp_path / "checkout"
    subprocess.run(["git", "init", "-q", str(checkout)], check=True)
    (checkout / RAW_QUOTE).parent.mkdir(parents=True)
    (checkout / RAW_QUOTE).write_text("contract_id,bid,ask\n", encoding="utf-8")
    subprocess.run(["git", "-C", str(checkout), "add", "--", RAW_QUOTE], check=True)
    return checkout


def test_the_fill_is_not_filled_with_an_alert_and_the_exits_still_run(root, tmp_path, alerts):
    decisions = Decisions()
    decisions.add(*decided(BOOK1_RULES, "t1", NORMAL), NORMAL)
    decisions.add(*decided(BOOK2_HYBRID, "b1", NORMAL), NORMAL)
    run, clock, *_ = daily_run(root, tmp_path, alerts, BOOKS, decisions, C4(), Rules())
    run.steps.sync = StagedRawQuoteSync(root, staged_checkout(tmp_path), alerts)
    before = PaperAccount(root, BOOK1_RULES).fills()
    log = run_day(run, clock, NORMAL)
    assert log.result("fills")["t1"]["reason"].startswith("not filled: the account write was refused")
    assert "refused before any fill was applied" in log.result("fills")["t1"]["reason"]
    assert log.result("fills")["b1"]["outcome"] == OUTCOME_OPENED
    assert PaperAccount(root, BOOK1_RULES).fills() == before  # nothing applied to book 1
    assert list(log.steps)[-1] == "exits" and BOOK1_RULES in log.result("exits")
    assert any("nifty_20261014_151500.csv" in sent for sent in alerts.sent)

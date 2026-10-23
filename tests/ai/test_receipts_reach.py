"""Story receipts-reach: the receipt search reaches back as far as the commit could have been pushed, not a fixed page
count (measured 22 Oct 2026: 10 pages of 100 covered only the last ~32 hours of this repository's pushes). A commit
older than the log's own end is named apart, and a committer date set later than the real push fails closed."""

from datetime import datetime, timedelta

import pytest

from fno.ai.receipts import GitHubActivityReceipts, ReceiptNotFound, ReceiptOutsideLog

NOW = datetime.fromisoformat("2026-10-22T23:00:00+00:00")
PUSHES = 3000  # c1 is the oldest commit; push i brought c(i-1) -> c(i), one every 10 minutes back from NOW


def moment(i: int) -> datetime:
    return NOW - timedelta(minutes=10 * (PUSHES - i))


class Chain:
    """c0 <- c1 <- ... <- c3000 on main; each commit made one minute before its push (or as `dates` says)."""

    def __init__(self, dates=None):
        self.dates = dates or {}

    def committed_at(self, commit):
        i = int(commit[1:])
        return self.dates.get(commit, moment(i) - timedelta(minutes=1))

    def is_ancestor(self, older, newer):
        return int(older[1:]) <= int(newer[1:])


class PagedLog:
    """GitHub's activity log of PUSHES pushes (from push `first`), 100 a page, newest first, with cursor links."""

    def __init__(self, first: int = 1):
        self.first, self.asked = first, 0

    def __call__(self, url, params=None, headers=None, timeout=None):
        self.asked += 1
        page = int(params.get("after", "0"))
        newest = PUSHES - 100 * page
        items = [{"before": f"c{i - 1}", "after": f"c{i}", "timestamp": moment(i).isoformat()}
                 for i in range(newest, max(newest - 100, self.first - 1), -1)]  # fmt: skip
        more = newest - 100 >= self.first
        return Response(items, f"https://api.github.com/repositories/1/activity?after={page + 1}" if more else None)


class Response:
    def __init__(self, items, next_url):
        self.items, self.status_code, self.ok = items, 200, True
        self.links = {"next": {"url": next_url}} if next_url else {}

    def json(self):
        return self.items


def test_a_push_1500_pushes_back_is_found_reading_only_the_pages_it_needs():
    log = PagedLog()
    receipts = GitHubActivityReceipts("exepex/trading", "token", Chain(), log)
    assert receipts.received_at(f"c{PUSHES - 1500}") == moment(PUSHES - 1500)
    # its commit's date minus a day's margin: 1,500 pushes plus 144 more (10 minutes apart), 17 pages, never all 30
    assert receipts.pages == 17 == log.asked
    assert receipts.received_at(f"c{PUSHES - 10}") == moment(PUSHES - 10)
    assert log.asked == 17  # a newer commit reuses the pages already read


def test_a_commit_older_than_the_logs_own_end_is_named_apart_from_no_push():
    receipts = GitHubActivityReceipts("exepex/trading", "token", Chain(), PagedLog(first=2001))
    with pytest.raises(ReceiptOutsideLog, match="activity log ends at .*before c1500 could be pushed"):
        receipts.received_at("c1500")
    covered = GitHubActivityReceipts("exepex/trading", "token", Chain(), PagedLog())
    with pytest.raises(ReceiptNotFound, match="no push of c9999"):
        covered.received_at("c9999")  # a commit no push brought, in a log that covers its time


def test_a_committer_date_set_after_the_real_push_finds_no_push_and_fails_closed():
    forged = {"c1500": moment(1500) + timedelta(days=3)}  # its push was 3 days before the date it claims
    receipts = GitHubActivityReceipts("exepex/trading", "token", Chain(forged), PagedLog())
    with pytest.raises(ReceiptNotFound):
        receipts.received_at("c1500")  # every later push's `before` already holds it: never a later push's time


def test_the_page_cap_stops_a_log_that_runs_on_and_says_so(monkeypatch):
    from fno.ai import activity_log
    from fno.ai.receipts import ReceiptUnavailable

    monkeypatch.setattr(activity_log, "PAGE_CAP", 3)
    receipts = GitHubActivityReceipts("exepex/trading", "token", Chain(), PagedLog())
    with pytest.raises(ReceiptUnavailable, match="ran past 3 pages"):
        receipts.received_at("c1")  # 30 pages back: stopped at the cap, never read on
    assert receipts.pages == 3

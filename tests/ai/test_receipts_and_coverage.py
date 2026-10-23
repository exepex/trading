"""Stories F1 and G5: the receipt time is GitHub's push time of the commit (its activity log), never the commit's own
date, and anything unclear fails closed; coverage counts pack days with a counted forecast (G5 criterion 3); the
workflow commits the pack alone before firing and the rules' records only after the collection (isolation)."""

from datetime import datetime

import pytest
import requests
import yaml

from fno.ai.coverage import coverage
from fno.ai.receipts import GitHubActivityReceipts, ReceiptAccessDenied, ReceiptNotFound, ReceiptUnavailable
from fno.constants import BOOK2_HYBRID, BOOK3_AI
from tests.ai.fakes import ROOT
from tests.ai.test_fire_and_collect import Desk

WORKFLOW = ROOT / ".github/workflows/forecast-capture.yml"


class Response:
    def __init__(self, items, status=200, next_url=None):
        self.items, self.status_code, self.ok = items, status, status < 400
        self.links = {"next": {"url": next_url}} if next_url else {}

    def json(self):
        return self.items


class History:
    """Which commit is in which: c1 <- c2 <- c3 on main."""

    order = ["c1", "c2", "c3"]

    def committed_at(self, commit):
        return datetime.fromisoformat("2026-10-13T09:40:00Z")

    def is_ancestor(self, older, newer):
        return older in self.order and newer in self.order and self.order.index(older) <= self.order.index(newer)


NUMERIC_NEXT = (
    "https://api.github.com/repositories/1414773933/activity?ref=refs%2Fheads%2Fmain&per_page=100&after=Y3Vyc29y"
)


def receipts(pages):
    calls = []

    def get(url, params=None, headers=None, timeout=None):
        calls.append((url, params, headers))
        return pages[len(calls) - 1]

    return GitHubActivityReceipts("exepex/trading", "token", History(), get), calls


def test_the_receipt_is_the_push_that_first_brought_the_commit_to_main():
    pushes = [
        {"before": "c2", "after": "c3", "timestamp": "2026-10-13T09:46:00Z"},
        {"before": "c1", "after": "c2", "timestamp": "2026-10-13T09:43:00Z"},
    ]
    found, calls = receipts([Response(pushes)])
    assert found.received_at("c2") == datetime.fromisoformat("2026-10-13T09:43:00Z")
    assert found.received_at("c3") == datetime.fromisoformat("2026-10-13T09:46:00Z")
    assert len(calls) == 1 and calls[0][1]["ref"] == "refs/heads/main"
    assert calls[0][2]["Authorization"] == "Bearer token"


def test_the_activity_log_is_read_across_pages():
    found, calls = receipts([
        Response([{"before": "c2", "after": "c3", "timestamp": "2026-10-13T09:46:00Z"}], next_url=NUMERIC_NEXT),
        Response([{"before": "c1", "after": "c2", "timestamp": "2026-10-13T09:43:00Z"}]),
    ])  # fmt: skip
    assert found.received_at("c2").minute == 43
    # page 2 is asked by owner/name with GitHub's cursor: the cloud proxy refuses numeric-ID paths (T1, 15 Oct)
    assert calls[1][0] == "https://api.github.com/repos/exepex/trading/activity"
    assert calls[1][1]["after"] == "Y3Vyc29y" and calls[1][1]["ref"] == "refs/heads/main"


def test_an_unreadable_log_or_an_unknown_commit_fails_closed():
    refused, _ = receipts([Response([], status=403)])
    with pytest.raises(ReceiptAccessDenied, match="access refused: HTTP 403"):  # an access problem, named apart
        refused.received_at("c2")
    failed, _ = receipts([Response([], status=500)])
    with pytest.raises(ReceiptUnavailable, match="HTTP 500") as raised:
        failed.received_at("c2")
    assert not isinstance(raised.value, ReceiptAccessDenied)
    empty, _ = receipts([Response([])])
    with pytest.raises(ReceiptNotFound, match="no push"):
        empty.received_at("c2")

    def down(*args, **kwargs):
        raise requests.ConnectionError("down")

    with pytest.raises(ReceiptUnavailable, match="not reached"):
        GitHubActivityReceipts("exepex/trading", "token", History(), down).received_at("c2")


def test_coverage_counts_pack_days_with_a_counted_forecast(tmp_path):
    desk = Desk(tmp_path)
    assert coverage(desk.root) == {BOOK2_HYBRID: (0, 1), BOOK3_AI: (0, 1)}  # not yet running: missing, not zero skill
    desk.fire()
    desk.answer(BOOK3_AI)
    desk.collect()
    assert coverage(desk.root) == {BOOK2_HYBRID: (0, 1), BOOK3_AI: (1, 1)}


def test_the_workflow_commits_the_pack_alone_before_firing_and_the_records_after_collecting():
    steps = [
        s.get("name", "") + "\n" + s.get("run", "")
        for s in yaml.safe_load(WORKFLOW.read_text())["jobs"]["capture"]["steps"]
    ]
    position = {key: next(i for i, s in enumerate(steps) if key in s) for key in
                ("fno forecast capture", "*_pack.json", "fno ai fire", "fno ai reveals-ready", "fno ai collect",
                 "git add research/forecasts #")}  # fmt: skip
    assert list(position.values()) == sorted(position.values())
    pack_step = steps[position["*_pack.json"]]
    assert "git add research/forecasts\n" not in pack_step and "_forecasts.csv" not in pack_step

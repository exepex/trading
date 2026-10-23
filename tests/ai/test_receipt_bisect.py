"""Story receipt-bisect: on plain pushes (each a fast-forward of main) "this push holds the commit" turns true once and
stays true, so the first push bringing a commit is found by halving and then checked exactly; a window with a force push
is read push by push, and a log that contradicts itself gives no receipt (fails closed)."""

from datetime import datetime, timedelta

import pytest

from fno.ai.receipts import GitHubActivityReceipts, ReceiptNotFound, ReceiptUnknown

START = datetime.fromisoformat("2026-10-16T00:00:00+00:00")


class Holds:
    """Which commit each commit holds: `held[c]` is the set of commits in c's history (c included); a dict-less
    `Line` holds every earlier cN. Counts the questions."""

    def __init__(self, held, date=START):
        self.held, self.date, self.asked = held, date, 0

    def committed_at(self, commit):
        return self.date

    def is_ancestor(self, older, newer):
        self.asked += 1
        return self.held(older, newer) if callable(self.held) else older in self.held.get(newer, ())


def line(older, newer):
    """c0 <- c1 <- ...: each cN holds every earlier one; any other name is in no history."""
    return older[1:].isdigit() and int(older[1:]) <= int(newer[1:])


def push(i, before, after, kind="push"):
    return {"activity_type": kind, "before": before, "after": after,
            "timestamp": (START + timedelta(minutes=i)).isoformat()}  # fmt: skip


class Log:
    def __init__(self, pushes):  # oldest first here; GitHub pages newest first
        self.items = list(reversed(pushes))

    def __call__(self, url, params=None, headers=None, timeout=None):
        return Page(self.items)


class Page:
    status_code, ok, links = 200, True, {}

    def __init__(self, items):
        self.items = items

    def json(self):
        return self.items


def receipts(held, pushes, date=START):
    history = Holds(held, date)
    return GitHubActivityReceipts("exepex/trading", "token", history, Log(pushes)), history


PUSHES = [push(i, f"c{i - 1}", f"c{i}") for i in range(1, 2001)]  # 2,000 plain pushes, one commit each


def test_a_push_among_2000_is_found_by_halving_with_about_a_dozen_questions():
    found, history = receipts(line, PUSHES)
    assert found.received_at("c1500") == START + timedelta(minutes=1500)
    assert history.asked <= 14  # 11 halvings and the exact check of the found push, never ~1,500 pushes read one by one


def test_the_first_push_of_the_window_can_be_the_one():
    found, _ = receipts(line, PUSHES)
    assert found.received_at("c1") == START + timedelta(minutes=1)


def test_a_commit_in_no_push_has_no_receipt():
    covered = START + timedelta(days=1, minutes=1)  # its date minus a day is the log's first push: a covered window
    found, _ = receipts(line, PUSHES, covered)
    with pytest.raises(ReceiptNotFound):
        found.received_at("stray")


def test_a_window_with_a_force_push_is_read_push_by_push():
    """c2 is pushed, a force push drops it (main back to c1), then c3 is built on c2 and pushed. Halving would land on
    the last push (its `before`, c1, does not hold c2) and give its later time; push by push finds the first."""
    held = {"c1": {"c1"}, "c2": {"c1", "c2"}, "c3": {"c1", "c2", "c3"}}
    pushes = [push(1, "c1", "c2"), push(2, "c2", "c1", "force_push"), push(3, "c1", "c3")]
    found, _ = receipts(held, pushes)
    assert found.received_at("c2") == START + timedelta(minutes=1)


def test_plain_pushes_that_contradict_themselves_give_no_receipt():
    """Plain pushes whose history goes back on itself (never expected from GitHub): no receipt, never a time."""
    held = {"c1": {"c1"}, "c2": {"c1", "c2"}, "c3": {"c1", "c2", "c3"}, "c4": {"c1", "c2", "c3", "c4"}}
    pushes = [push(1, "c1", "c2"), push(2, "c2", "c1"), push(3, "c3", "c4")]  # halving lands on push 3, held before
    found, _ = receipts(held, pushes)
    with pytest.raises(ReceiptUnknown, match="not one fast-forward line"):
        found.received_at("c2")


def test_two_pushes_in_one_second_are_ordered_by_githubs_id():
    """GitHub's timestamps are whole seconds and its pages are newest first; within a second its activity id gives the
    order. Without it, the later push is met first and its `before` already holds the commit: an unknown."""
    held = {"c1": {"c1"}, "c2": {"c1", "c2"}, "c3": {"c1", "c2", "c3"}}
    same = (START + timedelta(minutes=5)).isoformat()
    first = {"activity_type": "push", "id": 101, "before": "c1", "after": "c2", "timestamp": same}
    second = {"activity_type": "push", "id": 102, "before": "c2", "after": "c3", "timestamp": same}
    covered = START + timedelta(days=1, minutes=5)  # the search starts at the log's first entry: a covered window
    found, _ = receipts(held, [first, second], covered)  # Log pages them newest first: second, then first
    assert found.received_at("c2") == START + timedelta(minutes=5)
    assert found.received_at("c3") == START + timedelta(minutes=5)

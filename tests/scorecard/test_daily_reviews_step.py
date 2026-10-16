"""Story O1 (judge 214): E6's scorecards and automatic pauses run in the daily run after the exits. A catastrophic
loss pauses the version the same day through the real `ScorecardRun`; without a valid snapshot the step is refused
only when a position is open (it cannot be marked); with none open it is ok, and a closed loss still pauses."""

from datetime import datetime

from fno.constants import BOOK1_RULES, BOOK2_HYBRID, STEP_OK, STEP_REFUSED
from fno.daily.reviews import NOTHING_TO_MARK, UNMARKED, ReviewsStep, ScorecardReview
from fno.desk.run_log import RunLog
from fno.models import IST

from .conftest import START
from .history import trade
from .test_pauses import DAY, statuses


class Snapshots:
    def __init__(self):
        self.asked = []

    def snapshot(self, day, snapshot_id):
        self.asked.append((day, snapshot_id))
        return type("Snapshot", (), {"quotes": {}})()


def day_log(root, valid):
    at = datetime(2026, 10, 20, 15, 15, tzinfo=IST)
    RunLog.open(root, DAY).record("snapshot", at, at, {}, {"valid": valid, "snapshot_id": "nifty_20261020_151500"})


def step(root, make_run, snapshots):
    return ReviewsStep((ScorecardReview(make_run()),), snapshots, root, lambda specs: ["playbook/registry.csv"],
                       ("playbook/",))  # fmt: skip


def test_a_catastrophic_loss_pauses_the_version_the_same_day_and_commits_the_playbook(root, make_run, alerts):
    trade(root, BOOK2_HYBRID, "fly-a-v1", "t1", START, DAY, credit=50, debit=210)  # -Rs 10,400: over the cap
    day_log(root, valid=True)
    snapshots = Snapshots()
    done = step(root, make_run, snapshots).run(DAY)
    assert statuses(root)["fly-a"] == "paused" and statuses(root)["fly-b"] == "paper"
    assert done.result["status"] == STEP_OK and "fly-a-v1 paused in every book" in done.result["reason"]
    assert done.paths == ("playbook/registry.csv",) and snapshots.asked == [(DAY, "nifty_20261020_151500")]
    assert len(alerts.sent) == 1


def test_without_a_valid_snapshot_and_an_open_position_the_step_is_refused(root, make_run):
    """An open position cannot be marked, so its loss rules were not judged: refused (the next session blocks)."""
    trade(root, BOOK1_RULES, "fly-b-v1", "t2", START)  # still open
    day_log(root, valid=False)
    snapshots = Snapshots()
    done = step(root, make_run, snapshots).run(DAY)
    assert done.result["status"] == STEP_REFUSED and done.result["reason"] == UNMARKED.format(open=1)
    assert done.result["open_positions"] == 1 and snapshots.asked == []


def test_without_a_valid_snapshot_and_nothing_open_the_step_is_ok_and_a_closed_loss_still_pauses(root, make_run):
    """Judge 178 addendum 13, should-fix 10: no open position means nothing to mark, so nothing blocks tomorrow."""
    trade(root, BOOK2_HYBRID, "fly-a-v1", "t1", START, DAY, credit=50, debit=210)  # closed, over the cap
    day_log(root, valid=False)
    done = step(root, make_run, Snapshots()).run(DAY)
    assert done.result["status"] == STEP_OK and done.result["reason"].endswith(NOTHING_TO_MARK)
    assert statuses(root)["fly-a"] == "paused" and done.result["open_positions"] == 0

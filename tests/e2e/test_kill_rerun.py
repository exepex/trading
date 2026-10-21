"""Story O2, row "Partial run and rerun" (criterion 4): the routine's container dies right after each step of
`DAILY_RUN_STEPS` in turn (the count read from the tuple), a new run starts at the same clock, and no step runs twice.
The end state is compared with the no-failure twin: the committed tree and the private files in Drive.

Since O1's F1 (judge 421) a rerun resumes the 3 pm parts: one the killed run recorded is taken as recorded earlier,
one whose window is still open is restarted. So every kill reruns to the twin's bytes; only the run log differs, and
only in how each part ran (its `how`, its `started_at` and, for a part taken from the earlier run, its reason)."""

import subprocess

import pytest

from fno.constants import DAILY_RUN_STEPS, STEP_OK

from .harness import fixture_day
from .outside import Killed

AFTER_PARTS = DAILY_RUN_STEPS[DAILY_RUN_STEPS.index("quotes_done") :]  # the parts were committed by this run
AFTER_INDICES = DAILY_RUN_STEPS[DAILY_RUN_STEPS.index("snapshot") : DAILY_RUN_STEPS.index("quotes_done")]  # 15:15
BEFORE_INDICES = DAILY_RUN_STEPS[DAILY_RUN_STEPS.index("versions") : DAILY_RUN_STEPS.index("snapshot")]  # by 15:12
BEFORE_PARTS = DAILY_RUN_STEPS[: DAILY_RUN_STEPS.index("versions")]  # 14:33, before any part recorded
LOG = "journal/runs/{day}.json"
RESUMED = (
    [(step, dict.fromkeys(("nifty", "nse", "indices"), "earlier run")) for step in AFTER_INDICES]
    + [(step, {"nifty": "earlier run", "nse": "earlier run", "indices": "restarted"}) for step in BEFORE_INDICES]
    + [(step, dict.fromkeys(("nifty", "nse", "indices"), "restarted")) for step in BEFORE_PARTS]
)


def tree(day) -> dict[str, str]:
    """Every committed path and its blob hash at HEAD."""
    listing = subprocess.run(["git", "ls-tree", "-r", "HEAD"], cwd=day.root, capture_output=True, text=True).stdout
    return {line.split("\t", 1)[1]: line.split()[2] for line in listing.splitlines()}


@pytest.fixture(scope="module")
def twin(tmp_path_factory):
    """The uninterrupted day, once per test process: its tree, its Drive files and its run log."""
    with pytest.MonkeyPatch.context() as patch:
        day = fixture_day(tmp_path_factory.mktemp("twin"), patch)
        assert day.run() == (0, "day done")
        return tree(day), dict(day.drive.files), day.log()["steps"]


def killed_after(tmp_path, monkeypatch, step: str):
    day = fixture_day(tmp_path, monkeypatch)
    day.clock.kill_when = lambda: day.committed(f"Desk run {day.day} step {step}")
    with pytest.raises(Killed):
        day.run()
    return day, day.run()


def changed(before: dict, after: dict) -> set[str]:
    return {key for key in before.keys() | after.keys() if before.get(key) != after.get(key)}


def results(steps: dict) -> dict:
    return {name: step["result"] for name, step in steps.items()}


@pytest.mark.parametrize("step", AFTER_PARTS[:-1])  # the last step has nothing after it to kill
def test_a_kill_after_the_parts_ended_reruns_to_the_twin_s_bytes(tmp_path, monkeypatch, twin, step):
    day, end = killed_after(tmp_path, monkeypatch, step)
    assert (
        end == (0, "day done") and changed(twin[0], tree(day)) == set() and changed(twin[1], day.drive.files) == set()
    )


@pytest.mark.parametrize("step, how", RESUMED, ids=[step for step, _ in RESUMED])
def test_a_kill_before_quotes_done_reruns_to_the_twin_s_bytes_and_resumes_each_part(
    tmp_path, monkeypatch, twin, step, how
):
    day, end = killed_after(tmp_path, monkeypatch, step)
    assert end == (0, "day done") and day.slack.sent == []
    assert changed(twin[0], tree(day)) == {LOG.format(day=day.day)} and changed(twin[1], day.drive.files) == set()
    now, before = results(day.log()["steps"]), results(twin[2])
    parts = now.pop("quotes_done")["parts"]
    before.pop("quotes_done")
    assert now == before  # every other step exactly as on the twin day: none ran twice, none was skipped
    assert {name: (part["status"], part["how"]) for name, part in parts.items()} == {
        name: (STEP_OK, resumed) for name, resumed in how.items()}  # fmt: skip

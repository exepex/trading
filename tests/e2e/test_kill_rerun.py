"""Story O2, row "Partial run and rerun" (criterion 4): the routine's container dies right after each step of
`DAILY_RUN_STEPS` in turn (the count read from the tuple), a new run starts at the same clock, and no step runs twice.
The end state is compared with the no-failure twin: the committed tree and the private files in Drive.

What the 3 pm parts do on a rerun is the one named difference: a rerun whose log already holds `quotes` restarts none
(judge 178 note 4), so `quotes_done` is `failed` (`NOT_IN_THIS_RUN`, now alerted) and a part not ended before the kill
is lost. A kill before the parts recorded loses the day's quotes; that gap is named below, never expected."""

import subprocess

import pytest

from fno.constants import DAILY_RUN_STEPS, STEP_FAILED
from fno.daily.quote_steps import NOT_IN_THIS_RUN, NOT_IN_THIS_RUN_ALERT

from .harness import fixture_day
from .outside import Killed

AFTER_PARTS = DAILY_RUN_STEPS[DAILY_RUN_STEPS.index("quotes_done") :]  # the parts were committed by this run
AFTER_INDICES = DAILY_RUN_STEPS[DAILY_RUN_STEPS.index("snapshot") : DAILY_RUN_STEPS.index("quotes_done")]  # 15:15
BEFORE_INDICES = DAILY_RUN_STEPS[DAILY_RUN_STEPS.index("versions") : DAILY_RUN_STEPS.index("snapshot")]  # by 15:12
BEFORE_PARTS = DAILY_RUN_STEPS[: DAILY_RUN_STEPS.index("versions")]  # 14:33, before any part recorded
RERUN_LOSES_THE_DAY = (
    "gap (O2, 21 Oct; owner O1): a container killed before the 3 pm parts recorded kills them too, and the rerun "
    "starts none (its log holds `quotes`), so the day has no NIFTY or NSE record, no pack and no decision"
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


@pytest.mark.parametrize("step", AFTER_INDICES)
def test_a_kill_at_the_desk_reruns_every_later_step_once_and_names_the_parts(tmp_path, monkeypatch, twin, step):
    day, (code, line) = killed_after(tmp_path, monkeypatch, step)
    log_path = f"journal/runs/{day.day}.json"
    assert (code, line) == (1, "day done with problems: quotes_done")
    assert changed(twin[0], tree(day)) == {log_path} and changed(twin[1], day.drive.files) == set()
    now, before = results(day.log()["steps"]), results(twin[2])
    assert now.pop("quotes_done") == {"status": STEP_FAILED, "reason": NOT_IN_THIS_RUN}
    before.pop("quotes_done")
    assert now == before  # every other step exactly as on the twin day: none ran twice, none was skipped
    assert day.slack.sent == [NOT_IN_THIS_RUN_ALERT.format(day=day.day)]


@pytest.mark.parametrize("step", BEFORE_INDICES)
def test_a_kill_before_the_indices_ended_loses_only_the_indices_record(tmp_path, monkeypatch, twin, step):
    day, (code, _) = killed_after(tmp_path, monkeypatch, step)
    lost = {path for path in changed(twin[0], tree(day)) if not path.startswith("journal/runs/")}
    assert code == 1 and lost and all(any(n in p for n in ("banknifty", "finnifty", "midcpnifty")) for p in lost)
    assert results(day.log()["steps"])["pack"] == results(twin[2])["pack"]


@pytest.mark.xfail(strict=True, reason=RERUN_LOSES_THE_DAY)
@pytest.mark.parametrize("step", BEFORE_PARTS)
def test_a_kill_before_the_parts_recorded_still_records_the_day_s_quotes(tmp_path, monkeypatch, twin, step):
    day, _ = killed_after(tmp_path, monkeypatch, step)
    assert results(day.log()["steps"])["pack"] == results(twin[2])["pack"]

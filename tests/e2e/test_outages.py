"""Story O2, rows "Drive outage", "Slack outage" and "Groww or NSE failure": each outage through the real run, against
the no-failure twin. Every case runs twice, Slack up and Slack down (criterion 3): the alerts the owner gets are the
same multiset, each unsent one printed once for the routine's connector."""

from collections import Counter

import pytest

from fno.alerts.sender import NOT_SENT
from fno.constants import STEP_FAILED, STEP_OK, STEP_REFUSED

from .harness import fixture_day

UNSENT = NOT_SENT.format(reason="ConnectionError")


def unsent_texts(printed: str) -> list[str]:
    """The alerts the run printed as not sent ("<outcome> | <text>")."""
    return [line.split(" | ", 1)[1] for line in printed.splitlines() if line.startswith(f"{UNSENT} | ")]


def run_day(tmp_path, monkeypatch, capsys, slack_down: bool, outage):
    tmp_path.mkdir(parents=True, exist_ok=True)
    day = fixture_day(tmp_path, monkeypatch)
    day.slack.down = slack_down
    outage(day)
    result = day.run()
    return day, result, capsys.readouterr().out


def owner_alerts(day, printed: str) -> Counter:
    """What reached the owner: Slack's posts, or the printed unsent lines the routine posts with the connector."""
    return Counter(unsent_texts(printed)) if day.slack.down else Counter(day.slack.sent)


@pytest.fixture(params=[False, True], ids=["slack-up", "slack-down"])
def slack_down(request):
    return request.param


def no_ok_without_data(day) -> None:
    """O10's request (16 Oct): a step whose data did not land never records `ok`."""
    parts = day.step("quotes_done")["parts"]
    for name, part in parts.items():
        assert part["status"] != STEP_OK or part.get("commit") is not None, name


def groww_down(day):
    day.groww.down = True


def test_groww_down_all_day_gives_no_pack_no_decision_no_new_risk_and_alerts_each_once(
    tmp_path, monkeypatch, capsys, slack_down
):
    day, (code, line), printed = run_day(tmp_path, monkeypatch, capsys, slack_down, groww_down)
    assert (code, line) == (1, "day done with problems: book1, quotes_done")
    assert day.step("pack")["built"] is False
    assert day.step("decisions")["book1_rules"]["decision"] == "no decision (late)"
    assert day.step("snapshot")["valid"] is False and day.step("fills") == {}
    assert day.step("exits")["book1_rules"]["reviewed"] is True  # nothing open, nothing due: reviewed, not skipped
    assert day.step("quotes_done")["parts"]["nifty"]["status"] == STEP_FAILED
    alerts = owner_alerts(day, printed)
    assert sum(alerts.values()) == len(alerts) == 3  # NIFTY's part (O1, it had no alert of its own), Book 1, C3
    no_ok_without_data(day)


def test_the_twin_counts_match_with_slack_up_and_down(tmp_path, monkeypatch, capsys):
    """Criterion 3 directly: the same day's alerts, as one multiset, whether Slack took them or the run printed them."""
    up, _, printed_up = run_day(tmp_path / "up", monkeypatch, capsys, False, groww_down)
    down, _, printed_down = run_day(tmp_path / "down", monkeypatch, capsys, True, groww_down)
    assert owner_alerts(up, printed_up) == owner_alerts(down, printed_down) != Counter()
    assert down.slack.sent == [] and unsent_texts(printed_up) == []


def test_nse_failing_leaves_the_desk_as_on_the_twin_day(tmp_path, monkeypatch, capsys):
    twin, twin_result, _ = run_day(tmp_path / "twin", monkeypatch, capsys, False, lambda day: None)

    def nse_fails(day):
        day.children.script[("quotes", "record", "--source", "nse")] = type(day.children.script[("quotes", "record")])(
            lambda clock, staging: (1, ["recorded: - (0 contracts, complete=False) - NSE unreachable"])
        )

    day, (code, line), _ = run_day(tmp_path / "nse", monkeypatch, capsys, False, nse_fails)
    assert twin_result == (0, "day done") and (code, line) == (1, "day done with problems: quotes_done")
    for step in ("pack", "decisions", "snapshot", "fills", "exits", "trade_marks"):
        assert day.step(step).keys() == twin.step(step).keys(), step
    assert day.step("pack")["built"] is True and day.step("snapshot")["valid"] is True
    assert day.step("quotes_done")["parts"]["nse"]["status"] == STEP_FAILED


def test_drive_down_at_the_download_stops_the_desk_but_the_parts_still_record_and_the_next_session_runs(
    tmp_path, monkeypatch, capsys, slack_down
):
    def drive_down(day):
        day.drive.down = True

    day, (code, line), printed = run_day(tmp_path, monkeypatch, capsys, slack_down, drive_down)
    assert code == 1 and "run STOPPED at the download of the private paper records" in line
    assert line.endswith("; no card today") and day.log() == {}  # no step ran, so no log
    assert "3 pm quotes 2026-10-14 nse" in day.origin_subjects()  # NSE's public record still committed
    assert sum(owner_alerts(day, printed).values()) >= 1  # the next session: test_never_starts.py


CHILD_ALERT_TEXT_GAP = (
    "gap (O2, reported 16 Oct; owner A4/A4c): a child command prints only the outcome of an unsent alert "
    '("alert NOT sent: <reason>", fno/quotes/cli.py record_today), not its text, so the routine cannot post it'
)


def raw_down(day):
    day.drive.down_areas = {"raw"}


@pytest.mark.parametrize(
    "slack_down", [False, pytest.param(True, marks=pytest.mark.xfail(strict=True, reason=CHILD_ALERT_TEXT_GAP))],
    ids=["slack-up", "slack-down"],
)  # fmt: skip
def test_drive_down_for_raw_files_gives_no_canonical_no_pack_and_no_snapshot(tmp_path, monkeypatch, capsys, slack_down):
    day, (code, line), printed = run_day(tmp_path, monkeypatch, capsys, slack_down, raw_down)
    assert code == 1 and day.step("pack")["built"] is False and day.step("snapshot")["valid"] is False
    assert day.step("quotes_done")["parts"]["nifty"]["status"] in (STEP_FAILED, STEP_REFUSED)
    no_ok_without_data(day)
    assert any("raw quote file NOT saved" in text for text in owner_alerts(day, printed))

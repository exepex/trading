"""REH1, acceptance 1-4: with the mode set, every outside service the real composition roots build is its rehearsal
form; a planted break of each check is caught. Only the composition roots know the mode."""

import re
from pathlib import Path

from fno.constants import ENV_FNO_REHEARSAL
from fno.rehearsal.drive import DryrunDrive
from fno.rehearsal.guard import builders, problems
from fno.rehearsal.mode import Rehearsal
from fno.storage.wiring import OWNER_UPLOAD_SETTINGS

from .fakes import RecordingDrive

PACKAGE = Path(__file__).resolve().parents[2] / "fno"
# The composition roots (CLAUDE.md: each package's `wiring.py` or `<part>_wiring.py`), plus the entry point, the
# app's root, the command list (`rehearse check`), the daily command's `--rehearse` flag, the variable's name and the
# run log's registry of the rehearsal's message
ROOT_FILE = re.compile(r"(^|/|_)wiring\.py$")
ALSO = {
    "__main__.py",
    "cli.py",
    "composition.py",
    "daily/cli.py",
    "constants.py",
    "constants_operations.py",
    "daily/reason_codes.py",
}


def rehearsing(monkeypatch, tmp_path, slack=True):
    from datetime import date

    monkeypatch.setenv(ENV_FNO_REHEARSAL, Rehearsal.new(date(2026, 10, 23), tmp_path, tmp_path).to_env())
    if slack:
        monkeypatch.setenv("FNO_SLACK_BOT_TOKEN", "xoxb-test")


def test_with_the_mode_set_every_service_is_its_rehearsal_form(monkeypatch, tmp_path):
    rehearsing(monkeypatch, tmp_path)
    for name in OWNER_UPLOAD_SETTINGS:
        monkeypatch.setenv(name, "planted")
    monkeypatch.setattr("fno.storage.wiring.GoogleDriveUploadStore", lambda *a, **k: RecordingDrive())  # no sign-in
    assert problems() == []
    assert isinstance(builders()["the owner's Drive"][0](), DryrunDrive)


def test_without_the_mode_every_builder_gives_what_it_gives_today(monkeypatch):
    monkeypatch.delenv(ENV_FNO_REHEARSAL, raising=False)
    monkeypatch.setenv("FNO_SLACK_BOT_TOKEN", "xoxb-test")
    built = {name: type(build()).__name__ for name, (build, _) in builders().items()}
    assert built == {"the owner's Drive": "NoneType", "the #fno-desk alerts": "SlackChannelAlerts",
                     "the card's poster": "SlackCardPoster", "the lab's poster": "SlackFilesPoster",
                     "the 3 pm recorder": "QuoteSnapshotRecorder", "NSE's archive session": "PacedSession",
                     "A16's clock check": "ClockCheck", "the card's clocks": "ServerCardClocks"}  # fmt: skip


def test_each_planted_break_is_caught(monkeypatch, tmp_path):
    rehearsing(monkeypatch, tmp_path)
    services = builders()
    slack = [name for name in services if name != "the owner's Drive"]
    unlabelled = {name: (lambda: object(), services[name][1]) for name in slack}
    assert len(problems(unlabelled)) == 7  # three Slack ports, the 3 pm recorder, NSE's session, two clock checks
    assert problems({"drive": (lambda: object(), (DryrunDrive, type(None)))}) == [
        "rehearsal guard: drive is object, not its rehearsal form"]  # fmt: skip
    assert problems({}, probes=("https://api.anthropic.com/v1/messages",), is_allowed=lambda method, url: True) == [
        "rehearsal guard: a live call would be allowed: https://api.anthropic.com/v1/messages"]  # fmt: skip


def test_only_the_composition_roots_know_the_mode():
    mentions = re.compile(r"from \.+rehearsal|import fno\.rehearsal|ENV_FNO_REHEARSAL")
    outside = [p for p in PACKAGE.rglob("*.py") if "rehearsal" not in p.relative_to(PACKAGE).parts]
    knowing = sorted(str(p.relative_to(PACKAGE)) for p in outside if mentions.search(p.read_text()))
    assert [name for name in knowing if not ROOT_FILE.search(name) and name not in ALSO] == []

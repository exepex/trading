"""Story A13's daily job (G1 v3, responses 68-69): it appends only under a frozen protocol and a verified panel, reads
the first archived version of each input, checks inputs with named reasons, appends all pending sessions or none,
retries from the same day, and records each day's input versions. Real NSE file subsets (panel_fixtures.py) in a copy
of the fixture tree that plays Drive."""

import hashlib
import json
import shutil
from datetime import date, datetime
from pathlib import Path

import pytest
from panel_fixtures import FIXTURES, FixtureCalendar, build, panel_rows

from fno.forecast.freeze import NotFrozen
from fno.forecast.freeze_v2 import NotYetFrozen
from fno.models import IST
from fno.pipeline.panel_days import PanelDayJob, last_complete_day
from fno.pipeline.panel_wiring import first_archived_inputs
from fno.research_data.nifty_panel import NiftyPanelBuilder
from fno.research_data.panel_append import PanelAppender
from fno.research_data.panel_reader import read_nifty_panel
from fno.research_data.panel_store import MANIFEST_FILE, WARMUP_FILE
from fno.storage.raw_source import NseDailyFoSource, NseIndexCloseSource, NseLegacyFoSource
from fno.storage.raw_store import LocalFolderStore
from fno.storage.wiring import RAW_AREA, REVISIONS_AREA, build_file_exceptions
from tests.pipeline.fakes import RecordingAlerts

BASE, A, B = date(2020, 2, 1), date(2024, 1, 2), date(2024, 3, 2)  # A and B are pending; B is a Saturday session
CALENDAR = FixtureCalendar({BASE: "special", A: "regular", B: "special"})
RUN_TIME = lambda: datetime(2024, 3, 2, 21, 41, tzinfo=IST)  # noqa: E731
LATER = [{"sha256": "f" * 64, "available_from": "2024-03-02T23:20:00+05:30"}]


def _raw(drive: Path, source, day: date) -> Path:
    return drive / RAW_AREA / source.path_for(day)


def _official(drive: Path, *days: date) -> str:
    rows = [f"{d},regular,1.00,1.00,f,{hashlib.sha256(_raw(drive, NseIndexCloseSource, d).read_bytes()).hexdigest()}"
            for d in days]  # fmt: skip
    return "date,session,underlying,vix,index_file,index_sha256\n" + "".join(r + "\n" for r in rows)


@pytest.fixture
def setup(tmp_path):
    drive, panel = tmp_path / "drive", tmp_path / "panel"
    shutil.copytree(FIXTURES, drive)
    build(panel, BASE, calendar=CALENDAR)
    (panel / WARMUP_FILE).write_text(_official(drive, A, B))
    return drive, panel


def _job(drive, panel, alerts, freeze_check=lambda: None):
    fo, index = first_archived_inputs(LocalFolderStore(drive))
    builder = NiftyPanelBuilder(fo, index, CALENDAR, build_file_exceptions())
    lookup = lambda day, label: LATER if (day, label) == (A, "index-close") else []  # noqa: E731
    return PanelDayJob(builder, PanelAppender(panel), CALENDAR, freeze_check, lookup, alerts, RUN_TIME, lambda _: None)


def _manifest(panel) -> dict:
    return json.loads((panel / MANIFEST_FILE).read_text())


def test_pending_sessions_are_appended_once_with_their_input_versions(setup):
    drive, panel = setup
    alerts = RecordingAlerts()
    assert _job(drive, panel, alerts).run(B) == 0
    days = _manifest(panel)["days"]
    assert sorted(days) == ["2020-02-01", "2024-01-02", "2024-03-02"]
    entry = days[str(A)]
    assert entry["inputs_version"] == "first archived (A11 original)"
    assert entry["later_versions"] == {"fo": [], "index-close": LATER}
    assert entry["appended_at"] == entry["inputs_read_at"] == "2024-03-02T21:41:00+05:30"
    before = {p.name: p.read_bytes() for p in panel.iterdir()}
    assert _job(drive, panel, alerts).run(B) == 0  # nothing new: no byte changes
    assert {p.name: p.read_bytes() for p in panel.iterdir()} == before and alerts.lines == []


def test_the_first_archived_version_is_used_never_a_later_one(setup):
    drive, panel = setup
    first = _raw(drive, NseIndexCloseSource, A).read_bytes()
    revised = drive / REVISIONS_AREA / NseIndexCloseSource.path_for(A)
    revised.parent.mkdir(parents=True)
    revised.write_bytes(first + b"\n")  # a later NSE version, kept apart (A11)
    assert _job(drive, panel, RecordingAlerts()).run(B) == 0
    assert _manifest(panel)["days"][str(A)]["index_sha256"] == hashlib.sha256(first).hexdigest()


@pytest.mark.parametrize(
    "sources, day, reason",
    [((NseIndexCloseSource,), A, "index_close_missing"), ((NseDailyFoSource, NseLegacyFoSource), B, "fo_file_missing")],
)
def test_a_delayed_input_stops_with_its_reason_and_the_retry_appends_without_a_gap(setup, sources, day, reason):
    drive, panel = setup
    files = [f for f in (_raw(drive, s, day) for s in sources) if f.is_file()]  # every format that covers the day
    held = {f: f.read_bytes() for f in files}
    for f in files:
        f.unlink()  # NSE has not published it yet (or the archive step has not run)
    alerts = RecordingAlerts()
    assert _job(drive, panel, alerts).run(B) == 1
    assert _manifest(panel)["end"] == str(BASE)  # nothing appended: never A alone, never B over a missing A
    assert f"{day}: {reason}" in alerts.lines[0] and f"retries from {day}" in alerts.lines[0]
    for f, data in held.items():
        f.write_bytes(data)  # the morning retry finds it
    assert _job(drive, panel, alerts).run(B) == 0
    assert sorted(_manifest(panel)["days"]) == ["2020-02-01", "2024-01-02", "2024-03-02"]


def test_an_official_close_not_appended_yet_or_from_another_version_stops_the_run(setup):
    drive, panel = setup
    alerts = RecordingAlerts()
    (panel / WARMUP_FILE).write_text(_official(drive, A))  # O6 has not appended B yet
    assert _job(drive, panel, alerts).run(B) == 1 and "index_close_missing" in alerts.lines[-1]
    b_sha = hashlib.sha256(_raw(drive, NseIndexCloseSource, B).read_bytes()).hexdigest()
    (panel / WARMUP_FILE).write_text(_official(drive, A, B).replace(b_sha, "0" * 64))
    assert _job(drive, panel, alerts).run(B) == 1 and "index_close_differs" in alerts.lines[-1]
    assert _manifest(panel)["end"] == str(BASE)


def test_a_missing_freeze_record_is_an_alerting_failure_never_a_silent_stop(setup):
    """Judge 64 addendum 2: a scheduled job that silently appends nothing leaves Q5 stale about 21 sessions later."""

    def not_yet():
        raise NotYetFrozen("research/forecasts/FREEZE_v3.md does not exist")

    alerts = RecordingAlerts()
    assert _job(*setup, alerts, not_yet).run(B) == 1
    assert _manifest(setup[1])["end"] == str(BASE)
    assert len(alerts.lines) == 1 and "FREEZE_v3.md does not exist" in alerts.lines[0]


def test_a_failed_freeze_check_appends_nothing_and_alerts(setup):
    def changed():
        raise NotFrozen("frozen files changed after the freeze: fno/research_data/panel_append.py")

    alerts = RecordingAlerts()
    assert _job(*setup, alerts, changed).run(B) == 1
    assert _manifest(setup[1])["end"] == str(BASE) and "freeze check failed" in alerts.lines[0]


def test_a_crash_between_the_year_file_and_the_manifest_is_refused_and_recovers(setup, monkeypatch):
    drive, panel = setup
    committed = {p.name: p.read_bytes() for p in panel.iterdir()}  # what git holds
    original = Path.replace

    def crash_at_manifest(self, target):
        if Path(target).name == MANIFEST_FILE:
            raise OSError("runner lost")
        return original(self, target)

    monkeypatch.setattr(Path, "replace", crash_at_manifest)
    with pytest.raises(OSError):
        _job(drive, panel, RecordingAlerts()).run(B)
    monkeypatch.setattr(Path, "replace", original)
    alerts = RecordingAlerts()
    assert _job(drive, panel, alerts).run(B) == 1  # the start-of-run check names the mismatch
    assert "does not match" in alerts.lines[0] and "git checkout research/data/nifty-panel/" in alerts.lines[0]
    for p in panel.iterdir():
        p.unlink()
    for name, data in committed.items():  # git checkout research/data/nifty-panel/
        (panel / name).write_bytes(data)
    assert max(read_nifty_panel(panel).options) == BASE  # the committed panel reads as before
    assert _job(drive, panel, alerts).run(B) == 0 and _manifest(panel)["end"] == str(B)
    assert len(panel_rows(panel, 2024)) == _manifest(panel)["files"]["options_2024.csv.gz"]["rows"]


def test_the_panel_wiring_checks_the_panel_days_section(monkeypatch):
    """Judge 64 addendum 2: the composition root must ask for its own section, never the scoring one."""
    import fno.freeze_sections as sections
    from fno.pipeline.panel_wiring import require_v3_frozen

    asked = []
    monkeypatch.setattr(sections, "require_section_frozen", lambda root, commit, section: asked.append(section))
    require_v3_frozen()
    assert asked == [sections.PANEL_DAYS]


@pytest.mark.parametrize(
    "now, day",
    [
        (datetime(2026, 10, 14, 21, 41, tzinfo=IST), date(2026, 10, 14)),  # the evening run: today's session
        (datetime(2026, 10, 15, 12, 11, tzinfo=IST), date(2026, 10, 14)),  # the morning retry: yesterday's
        (datetime(2026, 10, 14, 20, 59, tzinfo=IST), date(2026, 10, 13)),  # before 21:00 today's files are not due
    ],
)
def test_a_run_appends_through_the_last_day_whose_files_are_due(now, day):
    assert last_complete_day(now) == day


@pytest.mark.parametrize("name", ["options_2020.csv.gz", "futures_2020.csv.gz"])
def test_a_mismatch_in_a_file_the_append_would_not_touch_is_refused_at_the_start(setup, name):
    """Only the start-of-run check sees this: the run would append 2024 days and never open the 2020 files."""
    drive, panel = setup
    (panel / name).write_bytes((panel / name).read_bytes() + b"planted")
    alerts = RecordingAlerts()
    assert _job(drive, panel, alerts).run(B) == 1
    assert f"{name} does not match manifest.json" in alerts.lines[0] and _manifest(panel)["end"] == str(BASE)

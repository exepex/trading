"""Story A16b, criterion 13 and criterion 3's calendar stop: exit codes, the dry-run folder rule, the default end date
and `backfill-verify`, with the composition root replaced by fakes."""

from datetime import date, datetime

import pytest

from fno.intraday import backfill_cli, backfill_wiring
from fno.models import IST
from fno.storage.wiring import REPOSITORY
from tests.intraday_backfill.fakes import FakeGroww, FakeNse, build, session_data, verifier

WEEK = [date(2026, 9, 28), date(2026, 9, 29), date(2026, 9, 30), date(2026, 10, 1)]


def _args(command="backfill", start=None, end=WEEK[3], dry_run=None):
    return type("Args", (), {"config": None, "intraday_cmd": command, "start": start, "end": end,
                             "dry_run": dry_run})()  # fmt: skip


@pytest.fixture
def wired(tmp_path, monkeypatch):
    """The CLI over a fake back-fill; `failing` makes the next build's Groww fail those calls."""
    state = {"failing": set()}

    def backfill(cfg, folder=None):
        fifteen, minutes, nse = session_data(WEEK)
        return build(tmp_path, FakeGroww(fifteen, minutes, state["failing"]), FakeNse(nse))

    monkeypatch.setattr("fno.config.load_app_config", lambda path: {})
    monkeypatch.setattr(backfill_wiring, "build_candle_backfill", backfill)
    monkeypatch.setattr(backfill_wiring, "build_deferral_log", lambda folder=None: backfill({}).deferrals)
    monkeypatch.setattr(backfill_wiring, "build_candle_verifier", lambda: verifier(backfill({})))
    monkeypatch.setattr("fno.intraday.backfill.SERIES_START", WEEK[0])
    return state


def test_a_complete_run_exits_0_and_prints_its_counts(wired, capsys):
    assert backfill_cli.cmd_backfill(_args()) == 0
    assert "sessions 4: 4 written now, 0 held before, 0 deferred" in capsys.readouterr().out


def test_a_deferred_session_exits_1_after_naming_it(wired, capsys):
    wired["failing"] = {("minutes", WEEK[2])}
    assert backfill_cli.cmd_backfill(_args()) == 1
    out = capsys.readouterr().out
    assert (
        f"DEFERRED {WEEK[2]}: Groww 1m {WEEK[2]}..{WEEK[2]}: GrowwAPIException (deferred by 1 run(s), never written)"
        in out
    )
    wired["failing"] = set()
    assert backfill_cli.cmd_backfill(_args()) == 0  # the next run writes it


def test_a_dry_run_folder_inside_the_repository_is_refused(wired, capsys):
    assert backfill_cli.cmd_backfill(_args(dry_run=REPOSITORY / "scratch")) == 1
    assert "must be outside the repository" in capsys.readouterr().out


def test_a_day_outside_the_calendar_stops_with_a7_s_message(wired, capsys):
    assert backfill_cli.cmd_backfill(_args(end=date(2027, 1, 5))) == 1
    out = capsys.readouterr().out
    assert out.startswith("candle back-fill stopped, nothing more written: 2027-01-01 is outside the calendar")
    assert "add every row of NSE's 2027 holiday circular" in out


def test_verify_exits_0_when_every_row_equals_its_copies_and_1_otherwise(wired, tmp_path, capsys):
    backfill_cli.cmd_backfill(_args())
    assert backfill_cli.cmd_backfill(_args("backfill-verify")) == 0
    assert capsys.readouterr().out.strip().endswith(backfill_cli.VERIFIED)
    next((tmp_path / "drive").rglob("*.json.gz")).write_bytes(b"changed")
    assert backfill_cli.cmd_backfill(_args("backfill-verify")) == 1
    assert "SHA-256 differs from its manifest row" in capsys.readouterr().out


@pytest.mark.parametrize(
    ("now", "expected"),
    [(datetime(2026, 10, 14, 20, 59, 59), date(2026, 10, 13)), (datetime(2026, 10, 14, 21, 0), date(2026, 10, 14))],
)
def test_the_default_end_is_today_only_from_21_00_ist_when_nse_s_file_is_out(now, expected):
    assert backfill_cli.latest_finished(now.replace(tzinfo=IST)) == expected

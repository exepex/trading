"""Judge 79's should-fixes for P8's flows: the reader never takes a later session from an old run-dated folder, and a
flows copy refused as covering a later session is named and skipped while the rest of the archive step goes on."""

from datetime import date
from pathlib import Path
from types import SimpleNamespace

from fno.market_read_models import cli
from fno.market_read_models.frame_inputs import FlowsReader
from fno.storage import wiring
from fno.storage.raw_store import LocalFolderStore
from fno.storage.session_filed_taker import FROM_THE_FUTURE, LaterSession
from fno.storage.snapshot_source import FiiDiiCashBySessionSource, FiiDiiCashSource, NsdlFpiDailySource
from fno.storage.wiring import build_session_calendar

FIXTURES = Path(__file__).parents[1] / "fixtures" / "flows"
D13, D14 = date(2026, 10, 13), date(2026, 10, 14)
CASH_13 = (FIXTURES / "fii-dii-cash_13102026.json").read_bytes()
CASH_14 = CASH_13.replace(b"13-Oct-2026", b"14-Oct-2026").replace(b"-1305.13", b"-900.00")
NSDL_13 = (FIXTURES / "fpi-daily-latest_13102026.html").read_bytes()


def test_an_old_run_dated_folder_holding_a_later_session_is_never_read_for_the_day(tmp_path):
    """A run-dated folder D can hold a copy covering a later session (a wrong clock); it is unread for D."""
    store = LocalFolderStore(tmp_path)
    store.put(FiiDiiCashSource.path_for(D13), CASH_14)  # filed under 13/, covers 14 Oct
    store.put(NsdlFpiDailySource.path_for(D13), NSDL_13)
    reader = FlowsReader(store, build_session_calendar())
    on_13 = reader.on(D13)
    assert list(on_13.cash) == []  # 14 Oct's -900.00 never reaches 13 Oct's page
    assert any("2026-10-13" in problem for problem in reader.problems(D13, on_13))  # named, not published empty
    assert [(c.day, c.fii.net) for c in reader.on(D14).cash] == [(D14, -900.0)]  # read for its own session


def later_session(day):
    """NSE already serves a later session than the re-run's day."""
    path = FiiDiiCashBySessionSource.path_for(D14)
    return LaterSession(FROM_THE_FUTURE.format(path=path, session=D14, day=day))


class Taker:
    def __init__(self, name, taken, failure):
        self.name, self.taken, self.failure = name, taken, failure

    def take(self, day):
        if self.name == "fii-dii-cash-by-session":
            raise self.failure(day)
        self.taken.append(self.name)
        return f"{self.name}: archived"


def archive_step(monkeypatch, failure):
    """Runs `_archive_session(13 Oct)` with the cash take failing as `failure`; (problem, lists taken, own lists)."""
    taken, own_lists = [], []
    complete = SimpleNamespace(fill=lambda start, end: SimpleNamespace(complete=True))
    monkeypatch.setattr(wiring, "build_manifest_recorder", lambda: SimpleNamespace(commit=lambda message: "committed"))
    monkeypatch.setattr(wiring, "build_librarian", lambda name, log: complete)
    monkeypatch.setattr(wiring, "build_snapshot_taker", lambda name: Taker(name, taken, failure))
    monkeypatch.setattr(cli, "_archive_revisions", lambda day: None)
    monkeypatch.setattr(cli, "_archive_own_lists", own_lists.append)
    return cli._archive_session(D13), taken, own_lists


def test_a_refused_flows_copy_is_named_and_the_rest_of_the_archive_step_goes_on(monkeypatch, capsys):
    problem, taken, own_lists = archive_step(monkeypatch, later_session)
    assert problem is None  # the publish step's own flows check decides, by name
    assert taken == [n for n in cli.DAILY_SNAPSHOTS if n != "fii-dii-cash-by-session"] and own_lists == [D13]
    assert "fpi-daily-by-session" in taken
    out = capsys.readouterr().out
    assert "fii-dii-cash-by-session: not archived (" in out and "after the run's day 2026-10-13; refused" in out


def test_a_copy_failing_its_check_still_stops_the_archive_step(monkeypatch):
    """Only a later-session refusal is skipped; a damaged copy is still the archive's problem, by name."""
    problem, taken, _ = archive_step(monkeypatch, lambda day: ValueError("fii-dii-cash: not NSE's FII/DII report"))
    assert problem == "ValueError: fii-dii-cash: not NSE's FII/DII report" and "fpi-daily-by-session" not in taken

"""Judge 66 item 4: the 13 Oct flows page was published EMPTY. FlowsReader started at the sources' first_day (14 Oct)
while the first copy was archived under 13/ (the publish run files its copy under the session it publishes). Now:
first_day is the first archived copy (held to the committed manifest), a 13 Oct-like archive gives non-empty flows
without look-ahead, and flows missing once the archive has begun stop the run with a named reason and an alert."""

from datetime import date
from pathlib import Path

from fno.market_read_models.frame_inputs import NO_CASH, NO_NSDL, FlowsReader
from fno.market_read_models.session_rows import IncompleteSession, SessionRowsBuilder
from fno.storage.manifest_folder import ManifestFolder
from fno.storage.raw_store import LocalFolderStore
from fno.storage.snapshot_source import FiiDiiCashSource, NsdlFpiDailySource
from fno.storage.wiring import MANIFEST_FOLDER, RUN_DATED_FLOWS, SNAPSHOT_SOURCES, build_session_calendar

from .test_market_contract_and_run import run

FIXTURES = Path(__file__).parents[1] / "fixtures" / "flows"
CALENDAR = build_session_calendar()
D13, D14 = date(2026, 10, 13), date(2026, 10, 14)
CASH = (FIXTURES / "fii-dii-cash_13102026.json").read_bytes()  # covers session 13 Oct
NSDL = (FIXTURES / "fpi-daily-latest_13102026.html").read_bytes()
FLOWS = (FiiDiiCashSource, NsdlFpiDailySource)


def archive(tmp_path, filed: dict[date, tuple[bytes, bytes]]) -> LocalFolderStore:
    store = LocalFolderStore(tmp_path)
    for day, (cash, nsdl) in filed.items():
        store.put(FiiDiiCashSource.path_for(day), cash)
        store.put(NsdlFpiDailySource.path_for(day), nsdl)
    return store


def test_first_day_is_never_after_the_first_archived_copy_in_the_committed_manifest():
    manifests = ManifestFolder(MANIFEST_FOLDER)
    for source in SNAPSHOT_SOURCES + RUN_DATED_FLOWS:
        days = [f.day for f in manifests.read(source)]
        assert not days or source.first_day <= min(days), source.__name__
    for source in FLOWS:  # the flows sources start exactly at their first copy: 13/ (judge 66 item 4)
        assert source.first_day == min(f.day for f in manifests.read(source)) == D13


def test_a_13_oct_like_archive_gives_non_empty_flows_for_13_oct(tmp_path):
    """Both copies were taken on 14 Oct and cover 13 Oct: 13/ by 13 Oct's publish run, 14/ by a flows-download run."""
    reader = FlowsReader(archive(tmp_path, {D13: (CASH, NSDL), D14: (CASH, NSDL)}), CALENDAR)
    flows = reader.on(D13)
    assert [(c.day, c.fii.net) for c in flows.cash] == [(D13, -1305.13)] and flows.nsdl
    assert [c.filed_on for c in flows.copies] == [D13, D13] and reader.problems(D13, flows) == []


def test_no_look_ahead_a_copy_filed_after_the_session_is_never_read_for_it(tmp_path):
    revised = CASH.replace(b"-1305.13", b"-1300.00")  # a later copy of 13 Oct's values, filed under 14 Oct
    reader = FlowsReader(archive(tmp_path, {D13: (CASH, NSDL), D14: (revised, NSDL)}), CALENDAR)
    assert [c.fii.net for c in reader.on(D13).cash] == [-1305.13]  # 14/ is after 13 Oct's publication: unread
    assert [c.fii.net for c in reader.on(D14).cash] == [-1300.0]  # for 14 Oct it is the latest copy of 13 Oct


def test_flows_missing_once_the_archive_has_begun_are_named(tmp_path):
    only_later = FlowsReader(archive(tmp_path, {D14: (CASH, NSDL)}), CALENDAR)  # copies exist, none filed by 13 Oct
    assert only_later.problems(D13, only_later.on(D13)) == [NO_CASH.format(day=D13, read=0), NO_NSDL.format(day=D13)]
    stale = FlowsReader(archive(tmp_path / "b", {D14: (CASH, NSDL)}), CALENDAR)  # 14/ holds 13 Oct's values only
    assert stale.problems(D14, stale.on(D14)) == [NO_CASH.format(day=D14, read=1)]
    before = FlowsReader(archive(tmp_path / "c", {}), CALENDAR)
    assert before.problems(date(2026, 10, 12), before.on(date(2026, 10, 12))) == []  # history not begun: no need


class NoFollowedList:
    def on_or_before(self, day):
        return None


def test_an_empty_flows_page_with_copies_archived_stops_the_run_and_alerts(tmp_path):
    store = archive(tmp_path / "raw", {D14: (CASH, NSDL)})  # copies exist, none can be read for 13 Oct
    rows = SessionRowsBuilder(store, CALENDAR, None, NoFollowedList(), None, None, FlowsReader(store, CALENDAR))
    reason = NO_CASH.format(day=D13, read=0)
    try:
        rows.build(D13)
    except IncompleteSession as stopped:
        assert stopped.missing[0] == reason
    else:
        raise AssertionError("the session was built without its flows")
    market, alerts, _ = run(tmp_path, rows)
    code, lines = market.run(D13)
    assert code == 1 and any("NOT published" in line or "failed" in line.lower() for line in lines)
    assert len(alerts.sent) == 1 and reason in alerts.sent[0]  # the named reason leads the alert

"""Story A4c: BANKNIFTY, FINNIFTY and MIDCPNIFTY recorded after NIFTY's push, inside 15:01-15:13 IST, paced; raw quote
files in Drive only; a quiet index is never a closed market; an index not recorded is "none" and alerted once."""

import csv
import io
import json
from datetime import datetime, time

from fno.models import IST
from fno.quotes.book_fetch import BookFetcher
from fno.quotes.expiry_listing import ExpiryListUnavailable
from fno.quotes.indices import INDEX_PER_SECOND, INDEX_WORKERS, IndexRecording, index_slot
from fno.quotes.indices_cli import record_indices
from fno.quotes.recorder import NOT_LISTED, earliest_waiting_start
from tests.quotes.drive_fakes import FakeDrive
from tests.quotes.index_fakes import FILE, SPOTS, Clock, IndexProvider, Listing, recorders
from tests.quotes.test_recorder_calendar import Alerts, NoCalls

TOO_EARLY = "not started: too early (before 14:41); a rerun from 14:41 to 15:13 records it"
AT_1500 = datetime(2026, 10, 13, 15, 0, 30, tzinfo=IST)
WINDOW_START, WINDOW_END = datetime(2026, 10, 13, 15, 1, tzinfo=IST), datetime(2026, 10, 13, 15, 13, tzinfo=IST)


def _run(tmp_path, start=AT_1500, **kwargs):
    clock = Clock(start)
    drive = kwargs.pop("drive", FakeDrive())
    recs = recorders(tmp_path, clock, drive=drive, **kwargs)
    return IndexRecording(recs, clock.now, clock.sleep).run(), recs, drive, clock


def _marker(tmp_path, name):
    return next(tmp_path.rglob(f"{name.lower()}_20261013.canonical")).read_text()


def _sent_times(drive):
    return [datetime.fromisoformat(r["request_sent_at"]) for data in drive.files.values()
            for r in csv.DictReader(io.StringIO(data.decode()))]  # fmt: skip


def test_each_index_is_recorded_with_drive_only_quotes_and_its_universe(tmp_path):
    results, _, drive, _ = _run(tmp_path)
    assert all(r.complete and r.rows == 12 for r in results.values())
    for name in SPOTS:
        assert _marker(tmp_path, name) == results[name].snapshot_id
        assert results[name].snapshot_id.startswith(f"{name.lower()}_20261013_150")
    assert len(drive.files) == 3 and not list(tmp_path.rglob("*.csv"))
    sidecars = [json.loads(p.read_text()) for p in tmp_path.rglob("*.meta.json")]
    assert {s["underlying"] for s in sidecars} == set(SPOTS) and all(s["universe"] == FILE for s in sidecars)
    assert not list(tmp_path.rglob("nifty_*"))  # NIFTY's files are not touched


def test_a_refused_index_ends_none_and_the_others_are_recorded(tmp_path):
    results, _, _, _ = _run(tmp_path, provider=IndexProvider(refuse={"FINNIFTY"}))
    assert not results["FINNIFTY"].complete and _marker(tmp_path, "FINNIFTY") == "none"
    assert results["BANKNIFTY"].complete and results["MIDCPNIFTY"].complete


def test_an_index_the_nse_file_no_longer_lists_is_one_incomplete_attempt_never_a_silent_skip(tmp_path):
    provider = IndexProvider()
    results, _, _, _ = _run(tmp_path, provider=provider, listing=Listing(listed={"BANKNIFTY", "FINNIFTY"}))
    assert results["MIDCPNIFTY"].reason == NOT_LISTED and _marker(tmp_path, "MIDCPNIFTY") == "none"
    sidecars = list(tmp_path.rglob("midcpnifty_*.meta.json"))
    assert len(sidecars) == 1 and NOT_LISTED in json.loads(sidecars[0].read_text())["failures"]
    assert not [c for c in provider.calls if c[0] == "MIDCPNIFTY"]


def test_an_unreadable_nse_file_is_reported_once_per_index_and_alerted(tmp_path, capsys):
    class NoFile(Listing):
        def listed(self, underlying, today):
            raise ExpiryListUnavailable("no NSE F&O file in the 7 days")

    clock, alerts = Clock(AT_1500), Alerts()
    code = record_indices(
        lambda: recorders(tmp_path, clock, listing=NoFile()), alerts, "cal.csv", clock.now, clock.sleep
    )
    assert code == 1 and len(alerts.sent) == 1 and len(list(tmp_path.rglob("*.meta.json"))) == 3
    assert "universe: ExpiryListUnavailable" in capsys.readouterr().out


def test_requests_start_inside_the_window_only(tmp_path):
    _, _, drive, _ = _run(tmp_path)
    assert min(_sent_times(drive)) >= WINDOW_START  # it waited for 15:01
    results, _, drive, _ = _run(tmp_path / "late", start=datetime(2026, 10, 13, 15, 12, 50, tzinfo=IST))
    assert all(t <= WINDOW_END for t in _sent_times(drive))  # nothing started after 15:13
    assert not any(r.complete for r in results.values())
    assert {_marker(tmp_path / "late", n) for n in SPOTS} == {"none"}


def test_after_the_window_nothing_is_asked_and_the_day_is_none(tmp_path):
    provider = IndexProvider()
    results, _, _, _ = _run(tmp_path, start=WINDOW_END, provider=provider)
    assert provider.calls == [] and {r.status for r in results.values()} == {"window closed"}
    assert {_marker(tmp_path, n) for n in SPOTS} == {"none"}


def test_a_quiet_index_is_recorded_complete_with_invalid_rows_and_no_alert(tmp_path, capsys):
    clock, alerts = Clock(AT_1500), Alerts()
    recs = recorders(tmp_path, clock, provider=IndexProvider(traded=False))
    assert record_indices(lambda: recs, alerts, "cal.csv", clock.now, clock.sleep) == 0
    assert alerts.sent == [] and "calendar says session" not in capsys.readouterr().out


def test_a_closed_day_asks_nothing_records_nothing_and_does_not_wait(tmp_path):
    clock, alerts = Clock(datetime(2026, 10, 20, 14, 35, tzinfo=IST)), Alerts()  # Dussehra; the routine starts 14:33
    recs = recorders(tmp_path, clock, provider=NoCalls())
    assert record_indices(lambda: recs, alerts, "cal.csv", clock.now, clock.sleep) == 0
    assert alerts.sent == [] and clock.slept == [] and not list(tmp_path.rglob("*"))


def test_one_alert_names_every_index_not_recorded(tmp_path, capsys):
    clock, alerts = Clock(AT_1500), Alerts()
    recs = recorders(tmp_path, clock, provider=IndexProvider(refuse={"FINNIFTY", "MIDCPNIFTY"}))
    assert record_indices(lambda: recs, alerts, "cal.csv", clock.now, clock.sleep) == 1
    (alert,) = alerts.sent
    assert "FINNIFTY (incomplete, canonical none)" in alert and "MIDCPNIFTY (incomplete, canonical none)" in alert
    assert "BANKNIFTY" not in alert
    lines = capsys.readouterr().out.splitlines()
    assert sum(line.startswith(("BANKNIFTY", "FINNIFTY", "MIDCPNIFTY")) for line in lines) == 3


def test_the_index_slots_are_paced_and_parallel_as_the_story_says():
    slot = index_slot("BANKNIFTY")
    assert (slot.workers, slot.per_second, INDEX_WORKERS, INDEX_PER_SECOND) == (3, 2.5, 3, 2.5)
    assert not slot.cross_check and slot.stop_requests_at == WINDOW_END.time() and slot.check_listed


def test_the_fetcher_waits_on_the_pacer_before_every_request_and_keeps_contract_order():
    class CountingPacer:
        waits = 0

        def wait(self):
            CountingPacer.waits += 1

    provider, clock = IndexProvider(), Clock(WINDOW_START)
    chain = provider.chain("BANKNIFTY", datetime(2026, 10, 27).date())
    contracts = sorted(chain.quotes)
    got = BookFetcher(provider, clock.now, workers=3, pacer=CountingPacer()).fetch(chain, contracts)
    assert CountingPacer.waits == len(contracts) and [(g.strike, g.kind) for g in got] == contracts


def test_a_request_may_start_at_the_window_end_but_not_after():
    provider = IndexProvider()
    chain = provider.chain("BANKNIFTY", datetime(2026, 10, 27).date())
    contract = sorted(chain.quotes)[:1]
    at_end = Clock(WINDOW_END, step=0)
    (got,) = BookFetcher(provider, at_end.now, stop_at=WINDOW_END).fetch(chain, contract)
    assert got.error is None and got.sent == WINDOW_END
    after = Clock(WINDOW_END, step=1)
    (got,) = BookFetcher(provider, after.now, stop_at=WINDOW_END).fetch(chain, contract)
    assert got.book is None and "window" in str(got.error)


def test_the_nse_file_is_read_and_parsed_once_for_all_indices(monkeypatch):
    from datetime import date

    from fno.quotes import expiry_listing
    from fno.quotes.expiry_listing import NseDailyFileExpiries
    from tests.quotes.test_monthly_contracts import Library

    parses = []

    def rows(name, data):
        parses.append(name)
        return [{"XpryDt": "2026-10-27", "FinInstrmTp": "IDO", "TckrSymb": name} for name in SPOTS]

    monkeypatch.setattr(expiry_listing, "read_fo_file", rows)
    library = Library([date(2026, 10, 12)])
    nse = NseDailyFileExpiries(library)
    for name in SPOTS:
        assert nse.listed(name, date(2026, 10, 13))[0] == [date(2026, 10, 27)]
        assert nse.listed_on(name, date(2026, 10, 12))[1] == [date(2026, 10, 27)]
    assert len(parses) == 1 and len(library.asked) == 1


def test_a_rerun_after_the_window_on_a_recorded_day_says_already_recorded(tmp_path):
    _run(tmp_path)  # 15:00:30: all three recorded
    clock, alerts = Clock(datetime(2026, 10, 13, 15, 20, tzinfo=IST)), Alerts()
    recs = recorders(tmp_path, clock, provider=NoCalls())
    assert record_indices(lambda: recs, alerts, "cal.csv", clock.now, clock.sleep) == 0 and alerts.sent == []


def test_an_index_whose_turn_comes_after_the_window_is_not_asked_anything(tmp_path):
    provider = IndexProvider()
    results, _, _, _ = _run(tmp_path, start=datetime(2026, 10, 13, 15, 12, 40, tzinfo=IST), provider=provider)
    asked = {call[0] for call in provider.calls}
    assert asked == {"BANKNIFTY"} and results["MIDCPNIFTY"].status == "window closed"


def _alerted(tmp_path, start, capsys, **kwargs):
    clock, alerts = Clock(start), Alerts()
    code = record_indices(lambda: recorders(tmp_path, clock, **kwargs), alerts, "cal.csv", clock.now, clock.sleep)
    return code, alerts.sent, capsys.readouterr().out.splitlines()


def test_a_run_too_early_says_not_started_and_never_canonical_none(tmp_path, capsys):
    """A4c-2 (DRY2 R1): at 14:38 the nifty part had died; 23 minutes early, nothing is recorded and no marker is
    written, so neither the lines nor the alert may say "canonical none"."""
    code, sent, lines = _alerted(tmp_path, datetime(2026, 10, 13, 14, 38, tzinfo=IST), capsys)
    assert code == 1 and len(sent) == 1 and "canonical none" not in sent[0]  # exit 1, one alert (judge 568 minor 2)
    assert all(f"{name} ({TOO_EARLY})" in sent[0] for name in SPOTS)
    index_lines = [line for line in lines if " too early: " in line]
    assert len(index_lines) == 3 and all(line.endswith(f"- {TOO_EARLY}") for line in index_lines)
    assert not list(tmp_path.rglob("*.canonical"))


def test_the_earliest_start_waits_and_one_second_before_it_is_too_early(tmp_path):
    """The fake clock moves 1 s at each read, so a clock set at 14:40:59 reads 14:41:00 first."""
    results, _, _, _ = _run(tmp_path, datetime(2026, 10, 13, 14, 40, 59, tzinfo=IST))
    assert all(r.complete for r in results.values())
    early, _, _, _ = _run(tmp_path / "early", datetime(2026, 10, 13, 14, 40, 58, tzinfo=IST))
    assert {r.status for r in early.values()} == {"too early"}


def test_an_index_closed_none_keeps_canonical_none_in_the_alert(tmp_path, capsys):
    code, sent, _ = _alerted(tmp_path, AT_1500, capsys, provider=IndexProvider(refuse={"FINNIFTY"}))
    assert code == 1 and "FINNIFTY (incomplete, canonical none)" in sent[0] and "BANKNIFTY" not in sent[0]


def test_the_earliest_waiting_start_is_the_window_less_a4_s_early_limit():
    """A4c-2: the one subtraction O1's start times build on (O1 adds its own margin)."""
    assert earliest_waiting_start(time(15, 1)) == time(14, 41) and earliest_waiting_start(time(14, 55)) == time(14, 35)

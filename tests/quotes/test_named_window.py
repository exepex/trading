"""Story A4e: a named window (protocol v4's 14:30-14:40) records a second NIFTY capture in its own dataset; no request
before its start or after its end; every pack field with its own times; A16's clock check in the sidecar; A4's default
capture unchanged."""

import csv
import io
import json
from datetime import datetime

from fno.intraday.clock import CLOCK_OK, CLOCK_SKEW, CLOCK_UNCHECKED
from fno.quotes.book_fetch import WindowEnded
from fno.quotes.capture_log import CaptureLog
from fno.quotes.recorder import DATASET, QuoteSnapshotRecorder
from fno.quotes.report import canonical_snapshots
from fno.storage.raw_store import LocalFolderStore
from tests.quotes.test_quote_recorder import Clock, FakeProvider
from tests.quotes.test_recorder_calendar import NoCalls
from tests.quotes.window_fakes import DAY, V4, V4_DATASET, SlowProvider, at, named_recorder


def _sidecar(folder, snapshot_id):
    return json.loads(next(folder.rglob(f"{snapshot_id}.meta.json")).read_text())


def _rows(drive):
    return [r for data in drive.files.values() for r in csv.DictReader(io.StringIO(data.decode()))]


def _times(rows, key):
    return [datetime.fromisoformat(r[key]) for r in rows]


def test_a_run_from_1405_waits_for_1430_and_asks_nothing_before_it(tmp_path):
    rec, clock, drive = named_recorder(tmp_path, at(14, 5))
    result = rec.record()
    assert result.complete and rec.canonical(DAY) == result.snapshot_id
    meta = _sidecar(tmp_path, result.snapshot_id)
    first = min(_times(meta["chains"], "request_sent_at") + _times(_rows(drive), "request_sent_at"))
    assert first >= at(14, 30) and datetime.fromisoformat(meta["levels_requested_at"]) >= at(14, 30)
    assert result.snapshot_id.startswith("nifty_20261013_1430")


def test_a_run_more_than_30_minutes_early_is_too_early_and_asks_nothing(tmp_path):
    rec, _, _ = named_recorder(tmp_path, at(13, 59), provider=NoCalls())
    assert rec.record().status == "too early" and not list(tmp_path.rglob("*"))


def test_an_incomplete_attempt_is_retried_inside_the_window(tmp_path):
    rec, _, _ = named_recorder(tmp_path, at(14, 30), provider=FakeProvider(fail_first=1))
    result = rec.record()
    assert result.complete and len(list(tmp_path.rglob("*.meta.json"))) == 2


def test_no_request_starts_after_1440_a_late_answer_keeps_its_time_and_the_day_ends_none(tmp_path):
    clock = Clock(at(14, 39, 40))
    rec, _, drive = named_recorder(tmp_path, None, provider=SlowProvider(clock, 6.0), clock=clock)
    result = rec.record()
    rows = _rows(drive)
    assert rows and max(_times(rows, "request_sent_at")) <= at(14, 40)
    assert max(_times(rows, "response_received_at")) > at(14, 40)  # kept with its real time, never relabelled
    meta = _sidecar(tmp_path, result.snapshot_id)
    assert any(WindowEnded.__name__ in f for f in meta["failures"]) and not result.complete
    assert rec.canonical(DAY) == "none"


def test_the_capture_is_in_its_own_dataset_and_default_readers_never_see_it(tmp_path):
    rec, _, drive = named_recorder(tmp_path, at(14, 30))
    result = rec.record()
    assert list(drive.files) == [f"{V4_DATASET}/2026/10/{result.snapshot_id}.csv"]  # the quote file in Drive only
    written = {p.relative_to(tmp_path).as_posix() for p in tmp_path.rglob("*") if p.is_file()}
    assert written == {
        f"{V4_DATASET}/2026/10/{result.snapshot_id}.meta.json",
        f"{V4_DATASET}/2026/10/nifty_20261013.canonical",
    }
    assert canonical_snapshots(tmp_path, LocalFolderStore(tmp_path)) == []  # A4's report reads the default dataset only


def test_each_chain_call_and_the_level_reads_carry_their_own_times(tmp_path):
    rec, _, drive = named_recorder(tmp_path, at(14, 30))
    meta = _sidecar(tmp_path, rec.record().snapshot_id)
    assert [c["expiry"] for c in meta["chains"]] == meta["expiries"] and all(
        c["spot"] == 22000.0 for c in meta["chains"]
    )
    for chain in meta["chains"]:
        assert chain["request_sent_at"] < chain["response_received_at"]
    requested, received = (datetime.fromisoformat(meta[k]) for k in ("levels_requested_at", "levels_received_at"))
    assert max(_times(meta["chains"], "response_received_at")) <= requested < received
    assert received <= min(_times(_rows(drive), "request_sent_at"))  # the levels are read before the first quote
    assert meta["india_vix_time"] == "13-Oct-2026 14:29" and "bid" not in meta["futures"][0]  # NSE: no futures bid/ask


def test_a_level_read_answered_after_the_window_keeps_its_real_later_time(tmp_path):
    rec, _, _ = named_recorder(tmp_path, at(14, 39, 30), level_delay=40.0)
    meta = _sidecar(tmp_path, rec.record().snapshot_id)
    assert datetime.fromisoformat(meta["levels_received_at"]) > at(14, 40)


def test_both_clock_readings_ok_give_clock_ok_with_the_worst_skew(tmp_path):
    rec, _, _ = named_recorder(tmp_path, at(14, 30), offsets=((0.0,), (0.0,)))
    meta = _sidecar(tmp_path, rec.record().snapshot_id)
    assert meta["clock_checks"] == [CLOCK_OK, CLOCK_OK] and meta["clock_status"] == CLOCK_OK
    assert meta["clock_worst_skew_seconds"] is not None and meta["clock_worst_skew_seconds"] <= 5


def test_a_skew_before_or_after_is_never_clock_ok(tmp_path):
    for offsets, expected in ((((9.0, 0.0),), [CLOCK_SKEW, CLOCK_OK]), (((0.0, 9.0),), [CLOCK_OK, CLOCK_SKEW])):
        folder = tmp_path / str(len(expected)) / expected[0]
        rec, _, _ = named_recorder(folder, at(14, 30), offsets=offsets)
        meta = _sidecar(folder, rec.record().snapshot_id)
        assert meta["clock_checks"] == expected and meta["clock_status"] == CLOCK_SKEW
        assert meta["clock_worst_skew_seconds"] > 5


def test_no_server_answering_is_unchecked_with_no_skew(tmp_path):
    rec, _, _ = named_recorder(tmp_path, at(14, 30), offsets=((None,),))
    meta = _sidecar(tmp_path, rec.record().snapshot_id)
    assert meta["clock_status"] == CLOCK_UNCHECKED and meta["clock_worst_skew_seconds"] is None


def test_a_missing_reading_keeps_its_place_and_is_never_clock_ok(tmp_path):
    for offsets, expected in (
        (((0.0, "raise"),), [CLOCK_OK, CLOCK_UNCHECKED]),
        ((("raise", 0.0),), [CLOCK_UNCHECKED, CLOCK_OK]),
    ):
        folder = tmp_path / expected[0]
        rec, _, _ = named_recorder(folder, at(14, 30), offsets=offsets)
        meta = _sidecar(folder, rec.record().snapshot_id)
        assert meta["clock_checks"] == expected and meta["clock_status"] == CLOCK_UNCHECKED


class SlowExpiries(FakeProvider):
    """The expiry list answers `delay` seconds late; the chain calls would then fall after the window's end."""

    def __init__(self, clock, delay):
        super().__init__()
        self.clock, self.delay, self.chain_calls = clock, delay, []

    def expiries(self, underlying):
        self.clock.sleep(self.delay)
        return super().expiries(underlying)

    def chain(self, underlying, expiry):
        self.chain_calls.append(self.clock.t)
        return super().chain(underlying, expiry)


def test_no_chain_or_level_request_starts_after_1440_even_when_the_expiry_list_is_slow(tmp_path):
    clock = Clock(at(14, 39, 50))
    provider = SlowExpiries(clock, 15.0)
    rec, _, drive = named_recorder(tmp_path, None, provider=provider, clock=clock)
    result = rec.record()
    meta = _sidecar(tmp_path, result.snapshot_id)
    assert provider.chain_calls == [] and not _rows(drive)  # the expiry list was asked at 14:39:5x, nothing after
    assert "levels_requested_at" not in meta and any("levels" in f for f in meta["levels_failures"])
    assert any(WindowEnded.__name__ in f for f in meta["failures"]) and rec.canonical(DAY) == "none"


def test_a_request_at_1440_00_is_allowed_and_one_at_1440_01_is_refused():
    for moment, allowed in ((at(14, 40), True), (at(14, 40, 1), False)):
        log = CaptureLog(None, lambda m=moment: m, V4.end)
        try:
            assert log.request_allowed() == moment and allowed
        except WindowEnded:
            assert not allowed


def test_the_default_capture_is_unchanged_no_window_keys_in_a4s_dataset(tmp_path):
    clock = Clock(at(14, 55))
    rec = QuoteSnapshotRecorder(FakeProvider(), LocalFolderStore(tmp_path), clock.now, clock.sleep)
    meta = _sidecar(tmp_path, rec.record().snapshot_id)
    assert not {"chains", "clock_status", "levels_received_at"} & set(meta)
    assert all(p.relative_to(tmp_path).as_posix().startswith(f"{DATASET}/") for p in tmp_path.rglob("*.json"))
    assert rec.window.start.hour == 14 and rec.window.start.minute == 55 and not rec.window.named
    assert V4.dataset(DATASET) == V4_DATASET


def test_retries_stop_at_1440_and_a_day_never_complete_ends_none(tmp_path):
    rec, _, _ = named_recorder(tmp_path, at(14, 30), provider=FakeProvider(fail_first=10_000))
    assert not rec.record().complete and rec.canonical(DAY) == "none"
    started = [datetime.fromisoformat(json.loads(p.read_text())["started_at"]) for p in tmp_path.rglob("*.meta.json")]
    assert len(started) > 1 and max(started) <= at(14, 40)  # retried inside the window, never after it


class CountingProvider(FakeProvider):
    def __init__(self):
        super().__init__()
        self.asked = []

    def expiries(self, underlying):
        self.asked.append("expiries")
        return super().expiries(underlying)


def test_an_attempt_whose_clock_check_runs_past_1440_asks_not_even_the_expiry_list(tmp_path):
    provider = CountingProvider()
    rec, _, _ = named_recorder(tmp_path, at(14, 39, 58), provider=provider)
    result = rec.record()
    assert provider.asked == [] and rec.canonical(DAY) == "none"
    assert any(WindowEnded.__name__ in f for f in _sidecar(tmp_path, result.snapshot_id)["failures"])

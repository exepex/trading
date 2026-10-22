"""A4h criteria 1-3 and 9: the read, its tries, the calendar and the gate, write-once records, and the 16:00 recheck."""

import json
from datetime import date, timedelta

import pytest

from fno.close_read.constants import READ, RECHECK
from fno.close_read.records import confirm_path, encode, raw_path, recheck_path, record_path
from fno.constants_operations import STEP_REFUSED
from fno.daily.steps import outcome
from tests.close_read.fakes import (
    DAY,
    HOLIDAY,
    LEVELS,
    MUHURAT,
    SPECIAL,
    Answers,
    Clock,
    MemoryStore,
    Official,
    answer,
    at,
    reader,
)


def _run(store, source, now, which=READ):
    lines, clock = [], Clock(now)
    code = reader(store, source, clock, lines=lines).run(which)
    return code, lines, clock


def test_a_read_at_15_40_records_the_raw_answer_and_the_day_s_record():
    store, source = MemoryStore(), Answers(answer())
    code, lines, _ = _run(store, source, at(15, 40))
    record = json.loads(store.files[record_path(DAY)])
    assert code == 0 and source.calls == 1 and raw_path(DAY, READ) in store.files
    assert record["indices"]["NIFTY 50"] == {"last": 22811.35, "open": 23016.0, "official_close": True}
    assert record["indices"]["INDIA VIX"]["official_close"] is False and record["provisional"] is True
    assert record["read"] == READ and record["nse_stamp"] == "21-Oct-2026 15:30"
    assert lines[-1].startswith("close read 2026-10-21: NIFTY 50, NIFTY BANK, INDIA VIX (list) recorded, NSE stamp ")
    assert "closes/2026/10/2026-10-21.json sha256 " in lines[-1]


def test_a_rerun_on_a_recorded_day_writes_nothing():
    store = MemoryStore()
    _run(store, Answers(answer()), at(15, 40))
    before, source = dict(store.files), Answers(answer())
    code, lines, _ = _run(store, source, at(19, 0))
    assert (code, lines[-1], source.calls, store.files) == (0, "close already read 2026-10-21", 0, before)


def test_three_tries_60_seconds_apart_then_not_read_and_a_fourth_is_never_sent():
    store, source = MemoryStore(), Answers(answer("19-Oct-2026 15:30"))
    code, lines, clock = _run(store, source, at(15, 40))
    assert (code, source.calls, clock.slept, store.files) == (1, 3, [60, 60], {})
    assert lines[-1] == "close not read: NSE stamp 19-Oct-2026 15:30 is not today's session"


def test_an_error_then_a_good_answer_is_recorded_and_the_error_s_message_is_withheld():
    source = Answers(RuntimeError("https://www.nseindia.com/api/allIndices 403"), answer())
    code, lines, clock = _run(MemoryStore(), source, at(15, 40))
    assert (code, source.calls, clock.slept) == (0, 2, [60])
    failed = Answers(RuntimeError("https://www.nseindia.com/api/allIndices 403"))
    code, lines, _ = _run(MemoryStore(), failed, at(15, 40))
    assert code == 1 and lines[-1] == "close not read: RuntimeError (message withheld)"


def test_before_the_gate_nothing_is_read_and_the_hand_run_says_too_early():
    source = Answers(answer())
    assert _run(MemoryStore(), source, at(15, 39))[:2] == (1, ["too early: before 15:40"]) and source.calls == 0
    assert _run(MemoryStore(), source, at(15, 59), RECHECK)[1] == ["too early: before 16:00"]


def test_a_closed_day_reads_nothing():
    source = Answers(answer())
    assert _run(MemoryStore(), source, at(15, 40, day=HOLIDAY))[:2] == (0, ["not a trading day"])
    assert source.calls == 0


@pytest.mark.parametrize(("day", "kind"), [(SPECIAL, "special"), (MUHURAT, "muhurat")])
@pytest.mark.parametrize("which", [READ, RECHECK])
def test_a_special_or_muhurat_day_writes_nothing_and_o1_records_it_refused_never_ok(day, kind, which):
    store, source = MemoryStore(), Answers(answer())
    code, lines, _ = _run(store, source, at(16, 0, day=day), which)
    assert code == 0 and source.calls == 0 and store.files == {}
    assert lines == [f"nothing written: close not read: {kind} session (no close time in the calendar)"]
    assert outcome(("closes", "read"), code, lines).result["status"] == STEP_REFUSED


def test_the_recheck_compares_each_index_with_the_first_read():
    store = MemoryStore()
    _run(store, Answers(answer()), at(15, 40))
    moved = {**LEVELS, "NIFTY BANK": (54976.95, 55707.85)}
    code, lines, _ = _run(store, Answers(answer(levels=moved)), at(16, 0), RECHECK)
    recheck = json.loads(store.files[recheck_path(DAY)])
    assert code == 0 and recheck["against_first"] == {"NIFTY 50": "same", "NIFTY BANK": "differs by 0.05",
                                                      "INDIA VIX": "same"}  # fmt: skip
    assert lines[-1].startswith("close recheck 2026-10-21: NIFTY 50 same, NIFTY BANK differs by 0.05, INDIA VIX same")
    assert raw_path(DAY, RECHECK) in store.files and json.loads(store.files[record_path(DAY)])["read"] == READ
    before, again = dict(store.files), Answers(answer())
    assert _run(store, again, at(16, 5), RECHECK)[1][-1] == "close already rechecked 2026-10-21"
    assert again.calls == 0 and store.files == before


def test_with_no_first_read_the_recheck_becomes_the_day_s_record():
    store = MemoryStore()
    code, lines, _ = _run(store, Answers(answer()), at(16, 0), RECHECK)
    assert code == 0 and json.loads(store.files[record_path(DAY)])["read"] == RECHECK
    assert lines[-1].startswith("close read 2026-10-21 at recheck (no first read to compare): ")
    assert recheck_path(DAY) not in store.files
    assert _run(store, Answers(answer()), at(16, 5), RECHECK)[1][-1] == "close already rechecked 2026-10-21"
    assert _run(store, Answers(answer()), at(16, 5), READ)[1][-1] == "close already read 2026-10-21"


class Down(Official):
    def closes(self, day):
        raise ConnectionError("https://nsearchives.nseindia.com/content/indices/ refused")


class DriveGetDown(MemoryStore):
    def get(self, path):
        raise ConnectionError("drive unreachable")


@pytest.mark.parametrize("store_kind", [MemoryStore, DriveGetDown])
def test_a_failing_confirm_of_an_earlier_day_never_stops_today_s_read(store_kind):
    """Judge 447 SF1: 19 Oct recorded but unconfirmed; the official archive (or Drive's get) fails; today is still
    read and recorded with exit 0, and its line comes before any confirm line."""
    store = store_kind()
    store.put(record_path(date(2026, 10, 19)), encode({"indices": {}}))
    official = Down() if store_kind is MemoryStore else Official({date(2026, 10, 19): {}})
    lines, clock = [], Clock(at(15, 46))
    code = reader(store, Answers(answer()), clock, official, lines=lines).run(READ)
    assert code == 0 and record_path(DAY) in store.files
    assert lines[0].startswith("close read 2026-10-21: ") and lines[1] == (
        "close confirm 2026-10-19: not confirmed (ConnectionError, message withheld); tried again next run"
    )
    if store_kind is DriveGetDown:
        return  # the recheck needs the first read from Drive: down, it fails loudly and O1 alerts
    recheck_lines = []
    assert reader(store, Answers(answer()), Clock(at(16, 0)), official, lines=recheck_lines).run(RECHECK) == 0
    assert recheck_lines[0].startswith("close recheck 2026-10-21: ") and recheck_path(DAY) in store.files


class SlowOfficial(Official):
    """Each archive call takes 300 s on the shared clock (judge 447 add. 1's retries)."""

    def __init__(self, clock, closes):
        super().__init__(closes)
        self.clock, self.calls = clock, 0

    def closes(self, day):
        self.calls += 1
        self.clock.now_at = self.clock.now_at + timedelta(seconds=300)
        return super().closes(day)


def test_a_slow_archive_never_turns_a_good_read_into_a_failure():
    """The confirm loop starts no new day 240 s after the run began, so the step ends inside O1's 600 s limit."""
    store = MemoryStore()
    earlier = (date(2026, 10, 16), date(2026, 10, 19))
    for day in earlier:
        store.put(record_path(day), encode({"indices": {}}))
    lines, clock = [], Clock(at(15, 40))
    official = SlowOfficial(clock, {})
    code = reader(store, Answers(answer()), clock, official, lines=lines).run(READ)
    assert code == 0 and record_path(DAY) in store.files and official.calls == 1
    assert lines[-1] == "close confirm: 1 earlier day(s) left for the next run (time budget)"
    assert (clock.now_at - at(15, 40)).total_seconds() <= 600


def test_the_newest_unconfirmed_day_takes_the_time_budget_first():
    """Judge 447 add. 2: while the archive keeps failing slowly on an old day, newer days are still confirmed."""
    store, newest = MemoryStore(), date(2026, 10, 19)
    for day in (date(2026, 10, 16), newest):
        store.put(
            record_path(day), encode({"indices": {n: {"last": 1.0} for n in ("NIFTY 50", "NIFTY BANK", "INDIA VIX")}})
        )
    clock = Clock(at(15, 40))
    official = SlowOfficial(clock, {newest: {"Nifty 50": 1.0, "Nifty Bank": 1.0, "India VIX": 1.0}})
    reader(store, Answers(answer()), clock, official, lines=[]).run(READ)
    assert confirm_path(newest) in store.files and confirm_path(date(2026, 10, 16)) not in store.files

"""G13 criteria 8-12: the live record. Not live, not today and closed days write nothing; a recorded day is never
rebuilt and its receipt is restored; a missing chain is recorded as missing; exits and last lines are the ones O1
reads (failed for problems, refused for nothing written); the command sends no alert of its own."""

import json
import math
from datetime import date, datetime, timedelta

from fno.forecast_v4_rules.series import DayValue
from fno.models import IST
from fno.price_distribution.build import DayBuilder
from fno.price_distribution.folders import live_path
from fno.price_distribution.recorder import HAND_RUN, NOT_TRADING, LiveRecorder
from fno.price_distribution.sources import ChainUnavailable
from fno.research_data.calendar import CsvSessionCalendar
from tests.price_distribution.builders import DAY, RATE, Chains, chain_day, drive_store

CALENDAR = CsvSessionCalendar(
    "date,kind,description,source_url\n2026-12-25,holiday,Christmas,https://example.invalid\n"
)
CLOSES = [DayValue(DAY - timedelta(days=900 - i), 22_000 * math.exp(0.01 * math.sin(i))) for i in range(900)]
NOW = datetime(2026, 10, 16, 15, 31, tzinfo=IST)
BOTH = {("NIFTY", DAY): chain_day(), ("BANKNIFTY", DAY): chain_day(underlying="BANKNIFTY")}


def recorder(tmp_path, chains=None, live_from=DAY, now=NOW, fail=False, source=None):
    store, drive, receipts = drive_store(tmp_path, fail)
    source = source or Chains(BOTH if chains is None else chains)
    built = LiveRecorder(source, DayBuilder(CALENDAR, RATE, CLOSES, "c0" * 32), store, CALENDAR,
                         ("NIFTY", "BANKNIFTY"), live_from, lambda: now)  # fmt: skip
    return built, drive, receipts, source


def test_a_good_day_writes_one_live_file_per_underlying_with_receipts(tmp_path):
    built, drive, receipts, source = recorder(tmp_path)
    code, lines = built.record(DAY)
    assert (code, lines[-1]) == (0, "recorded")
    for underlying in ("NIFTY", "BANKNIFTY"):
        record = json.loads(drive.files[f"data/{live_path(underlying, DAY)}"])
        assert record["label"] == "live" and record["made_at"] == NOW.isoformat()
        assert receipts.read(f"data/{live_path(underlying, DAY)}") is not None
    assert source.calls == [("NIFTY", DAY), ("BANKNIFTY", DAY)]  # the day's chain only


def test_not_live_before_its_date_or_without_one_and_not_today_write_nothing(tmp_path):
    for live_from, day in (
        (None, DAY),
        (DAY + timedelta(days=1), DAY),
        (DAY - timedelta(days=5), DAY - timedelta(days=1)),
    ):
        built, drive, _, source = recorder(tmp_path / str(day) / str(live_from), live_from=live_from)
        code, lines = built.record(day)
        assert code == 0 and lines[-1].startswith("nothing written:") and not drive.files and not source.calls


def test_the_live_date_itself_is_live(tmp_path):
    assert recorder(tmp_path, live_from=DAY)[0].record(DAY)[0] == 0


def test_a_closed_day_writes_nothing(tmp_path):
    holiday = date(2026, 12, 25)
    built, drive, _, _ = recorder(tmp_path, live_from=DAY, now=datetime(2026, 12, 25, 15, 31, tzinfo=IST))
    assert built.record(holiday) == (0, [NOT_TRADING]) and not drive.files


def test_a_recorded_day_is_never_rebuilt_and_a_lost_receipt_is_restored(tmp_path):
    built, drive, receipts, _ = recorder(tmp_path)
    built.record(DAY)
    first = dict(drive.files)
    path = f"data/{live_path('NIFTY', DAY)}"
    receipts.file_for(path).unlink()  # the receipt commit failed
    later, *_ = recorder(tmp_path, now=NOW + timedelta(minutes=20))
    later.store = built.store
    code, lines = later.record(DAY)
    assert (code, lines) == (0, ["NIFTY: already recorded", "BANKNIFTY: already recorded", "recorded"])
    assert drive.files == first and receipts.read(path) is not None


def test_one_missing_chain_is_recorded_missing_and_the_step_fails_with_one_line(tmp_path):
    built, drive, _, _ = recorder(tmp_path, chains={("NIFTY", DAY): chain_day()})
    code, lines = built.record(DAY)
    assert code == 1 and lines[-1] == "written with problems: BANKNIFTY no canonical 3 pm chain"
    missing = json.loads(drive.files[f"data/{live_path('BANKNIFTY', DAY)}"])
    assert missing["status"] == "missing" and missing["problems"] == ["no canonical 3 pm chain"]


def test_an_unreadable_chain_writes_no_file_so_a_rerun_can_record_it(tmp_path):
    chains = {("NIFTY", DAY): chain_day(), ("BANKNIFTY", DAY): ChainUnavailable("groww raw quote file unreadable: x")}
    built, drive, _, _ = recorder(tmp_path, chains=chains)
    code, lines = built.record(DAY)
    assert code == 1 and "BANKNIFTY groww raw quote file unreadable: x" in lines[-1]
    assert "problem: BANKNIFTY groww raw quote file unreadable: x" in lines
    assert f"data/{live_path('BANKNIFTY', DAY)}" not in drive.files
    built.source = Chains(BOTH)  # Drive is back
    assert built.record(DAY) == (0, ["NIFTY: already recorded", "BANKNIFTY: recorded (0 problems)", "recorded"])


def test_every_chain_unreadable_is_a_failure_with_nothing_written(tmp_path):
    down = ChainUnavailable("groww raw quote file unreadable: x")
    built, drive, _, _ = recorder(tmp_path, chains={("NIFTY", DAY): down, ("BANKNIFTY", DAY): down})
    code, lines = built.record(DAY)
    assert code == 1 and lines[-1].startswith("nothing written: ") and not drive.files


def test_one_failing_build_never_loses_the_other_underlyings(tmp_path):
    class Breaking(DayBuilder):
        def build(self, chain, label, made_at):
            if chain.underlying == "BANKNIFTY":
                raise ValueError("Out of range float values are not JSON compliant")
            return super().build(chain, label, made_at)

    built, drive, _, _ = recorder(tmp_path)
    built.builder = Breaking(CALENDAR, RATE, CLOSES, "c0" * 32)
    code, lines = built.record(DAY)
    assert code == 1 and "BANKNIFTY build failed (ValueError)" in lines[-1]
    assert list(drive.files) == [f"data/{live_path('NIFTY', DAY)}"]


def test_a_hand_run_never_writes_live_rows(tmp_path):
    built, drive, _, source = recorder(tmp_path)
    code, lines = built.record(DAY, live=False)
    assert code == 0 and lines == [HAND_RUN] and not drive.files and not source.calls


def test_problems_inside_a_chain_fail_the_step_but_the_files_are_written(tmp_path):
    chains = {("NIFTY", DAY): chain_day(spot=None), ("BANKNIFTY", DAY): chain_day(underlying="BANKNIFTY")}
    built, drive, _, _ = recorder(tmp_path, chains=chains)
    code, lines = built.record(DAY)
    assert code == 1 and lines[-1].startswith("written with problems: NIFTY ") and "no spot" in lines[-1]
    assert len(drive.files) == 2


def test_no_chain_for_any_underlying_is_refused_and_writes_nothing(tmp_path):
    built, drive, _, _ = recorder(tmp_path, chains={})
    code, lines = built.record(DAY)
    assert code == 0 and lines[-1].startswith("nothing written: no 3 pm chain for any underlying") and not drive.files


def test_a_drive_failure_leaves_no_receipt_and_raises_to_the_command(tmp_path):
    built, _, receipts, _ = recorder(tmp_path, fail=True)
    try:
        built.record(DAY)
    except RuntimeError as error:
        assert "Drive is down" in str(error)
    else:
        raise AssertionError("a Drive failure must stop the command")
    assert receipts.under("data") == []


def test_a_rerun_of_a_problem_day_still_fails_with_the_stored_problems(tmp_path):
    """Judge 310: a stored `missing` record and a record with problems count again, so O8 never sees a false ok."""
    chains = {("NIFTY", DAY): chain_day(spot=None)}  # NIFTY written with problems, BANKNIFTY recorded missing
    built, drive, _, _ = recorder(tmp_path, chains=chains)
    first_code, _ = built.record(DAY)
    files = dict(drive.files)
    code, lines = built.record(DAY)
    assert (first_code, code) == (1, 1) and drive.files == files
    assert lines[0].startswith("NIFTY: already recorded with ") and lines[1] == (
        "BANKNIFTY: already recorded with 1 problems"
    )
    assert lines[-1].startswith("written with problems: NIFTY ") and "BANKNIFTY no canonical 3 pm chain" in lines[-1]

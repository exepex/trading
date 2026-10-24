"""Criteria 2, 3, 8, 9 (story MS-P0b) through one real slot runner over planted faults."""

from datetime import datetime, time

import pytest

from fno.capture_probes.constants import DAILY_CAP, FUTURES, SLOT_BUDGET, Source
from fno.capture_probes.counts import DayCounts, SourceSlot
from fno.capture_probes.dry_run import near_expiry
from fno.capture_probes.slot import PLANNED_ROWS
from fno.models import IST

from .fakes import SESSION, GrowwError, GrowwRateLimitedStub, MemoryStore, RecordingPublisher, Rig, status

SLOT = "10:07"
DEADLINE = datetime.combine(SESSION, time(10, 13), IST)


def run_slot(rig, counts=None):
    counts = counts or rig.counts()
    return rig.runner.run(SESSION, SLOT, counts, DEADLINE), counts


def test_a_clean_slot_reads_the_whole_budget_and_saves_one_file_per_source(tmp_path):
    rig = Rig(tmp_path)
    lines, counts = run_slot(rig)
    assert rig.groww.calls == SLOT_BUDGET[Source.GROWW] + 6 and rig.nse.calls == SLOT_BUDGET[Source.NSE]
    assert sorted(rig.store.files) == ["school/p0b/groww/2026-10-29/1007.jsonl.gz",
                                       "school/p0b/nse/2026-10-29/1007.jsonl.gz"]  # fmt: skip
    assert all(entry.used == entry.reserved and entry.rows == PLANNED_ROWS for entry in counts.slots[SLOT].values())
    assert rig.publisher.calls == [f"{SESSION} slot 10:07 reserved", f"{SESSION} slot 10:07 counts"]
    assert rig.alerts.sent == [] and not counts.stops


def test_a_reservation_that_cannot_be_pushed_starts_no_request(tmp_path):
    rig = Rig(tmp_path, publisher=RecordingPublisher(fail_on=(1,)))
    lines, counts = run_slot(rig)
    assert rig.groww.calls == 0 and rig.nse.calls == 0
    assert lines[0].startswith("p0b slot 10:07: reservation not pushed") and SLOT not in counts.slots
    assert SLOT not in rig.counts().slots


def test_a_run_killed_mid_slot_leaves_its_whole_reservation_counted(tmp_path):
    rig = Rig(tmp_path, groww_faults={3: KeyboardInterrupt()})  # killed after its third request
    with pytest.raises(KeyboardInterrupt):
        run_slot(rig)
    reread = Rig(tmp_path).counts()  # the rerun reads the file the dead run left
    assert reread.spent(Source.GROWW) == SLOT_BUDGET[Source.GROWW] + 6 != 3
    assert reread.spent(Source.NSE) == SLOT_BUDGET[Source.NSE]


@pytest.mark.parametrize("source", list(Source))
def test_the_request_past_the_daily_cap_is_never_sent(tmp_path, source):
    rig = Rig(tmp_path)
    rig.tools.groww.expiries = dict.fromkeys(FUTURES, near_expiry(SESSION))  # looked up: a plain slot budget
    counts = DayCounts(str(SESSION), {"09:00": {source: SourceSlot(reserved=DAILY_CAP[source] - 5)}})
    lines, counts = run_slot(rig, counts)
    calls = rig.groww.calls if source is Source.GROWW else rig.nse.calls
    assert calls == 5 and counts.spent(source) == DAILY_CAP[source]
    assert "daily cap reached" in counts.stops[source]
    assert rig.log.rows()[0].kind == "cap_reached"


def test_groww_s_first_429_stops_it_for_the_day_with_one_alert_and_one_o10_row(tmp_path):
    rig = Rig(tmp_path, groww_faults={8: GrowwRateLimitedStub("429")})
    lines, counts = run_slot(rig)
    assert rig.groww.calls == 8
    assert counts.stops[Source.GROWW] == "p0b groww stopped for the day at 10:07: HTTP 429"
    assert rig.alerts.sent == [counts.stops[Source.GROWW]]
    assert [(r.job, r.step, r.kind) for r in rig.log.rows()] == [("school-p0b", "groww", "rate_limited")]
    assert rig.nse.calls == SLOT_BUDGET[Source.NSE]  # NSE's part still runs


@pytest.mark.parametrize("code", [401, 403, 404])
def test_any_other_4xx_from_nse_stops_it_for_the_day(tmp_path, code):
    rig = Rig(tmp_path, nse_faults={2: status(code)})
    lines, counts = run_slot(rig)
    assert rig.nse.calls == 2 and counts.stops[Source.NSE].endswith(f"HTTP {code}")
    assert rig.log.rows()[0].kind == "blocked"


@pytest.mark.parametrize("fault", ["html", "empty", "wrong shape"])
def test_a_200_that_is_not_the_expected_json_stops_nse(tmp_path, fault):
    from fno.capture_probes.dry_run import MadeUpResponse

    answer = {"html": MadeUpResponse(None), "empty": MadeUpResponse({}), "wrong shape": MadeUpResponse({"x": 1})}
    rig = Rig(tmp_path, nse_faults={3: answer[fault]})
    lines, counts = run_slot(rig)
    assert rig.nse.calls == 3 and counts.stops[Source.NSE].endswith("answer is not the expected JSON")


def test_a_stopped_source_is_not_asked_again_in_a_later_slot(tmp_path):
    rig = Rig(tmp_path, nse_faults={1: status(403)})
    _, counts = run_slot(rig)
    rig.runner.run(SESSION, "11:37", counts, datetime.combine(SESSION, time(11, 43), IST))
    assert rig.nse.calls == 1 and Source.NSE not in counts.slots["11:37"]


def test_an_unplaceable_groww_error_fails_closed_and_keeps_no_message(tmp_path):
    rig = Rig(tmp_path, groww_faults={1: GrowwError()})
    lines, counts = run_slot(rig)
    assert rig.groww.calls == 1 and counts.stops[Source.GROWW].endswith("GrowwError")
    assert "SECRET-IN-MESSAGE" not in " ".join(lines) + counts.to_json()


def test_a_groww_server_error_is_retried_once_then_the_row_is_missing(tmp_path):
    rig = Rig(tmp_path, groww_faults={7: GrowwError("503"), 8: GrowwError("503")})
    _, counts = run_slot(rig)
    entry = counts.slots[SLOT][Source.GROWW]
    assert entry.refusals == {"HTTP 503": 2} and not counts.stops
    # NIFTY's future is missing, and the retry spent a request of the fixed reservation, so the slot's last leg is
    # unread too: the reservation is a hard ceiling, retries included
    assert entry.quality["missing"] == 2 and entry.used == entry.reserved


def test_a_drive_conflict_is_named_and_a_failed_write_counted(tmp_path):
    lines, counts = run_slot(Rig(tmp_path / "a", store=MemoryStore(conflict=True)))
    assert any("Drive already holds other bytes" in line for line in lines)
    _, counts = run_slot(Rig(tmp_path / "b", store=MemoryStore(fail=True)))
    assert {entry.drive for entry in counts.slots[SLOT].values()} == {"failed"}


def test_rows_carry_the_eight_fields_and_their_quality(tmp_path):
    import gzip
    import json

    rig = Rig(tmp_path)
    run_slot(rig)
    lines = [json.loads(x) for x in gzip.decompress(rig.store.files["school/p0b/nse/2026-10-29/1007.jsonl.gz"])
             .decode().splitlines()]  # fmt: skip
    rows = [line["row"] for line in lines if "row" in line]
    assert len(rows) == PLANNED_ROWS
    fields = {"instrument", "contract", "expiry", "lot", "source_time", "first_seen", "raw_sha256", "quality"}
    assert all(fields <= set(row) for row in rows)
    sbin = [row for row in rows if row["instrument"] == "SBIN"]
    assert all("lot_unknown" in row["quality"] for row in sbin)
    puts = [row for row in rows if row["kind"] == "option" and row["contract"].endswith("PE")]
    assert puts and all("one_sided" in row["quality"] for row in puts)  # the made-up puts have no bid

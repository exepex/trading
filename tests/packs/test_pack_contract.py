"""Judge 72's findings on E2: the opportunity set reads each version's status at the start of the day (criterion 5);
point-in-time edges of the source contract (criterion 4); a session day without its snapshot is never frozen; and the
small contract checks (duplicate names, past events, 260 closes, journal paths, provenance hashes)."""

import hashlib
import json
from datetime import date, datetime, timedelta

import pytest

from fno.desk.common_pack import CommonPackBuilder
from fno.desk.pack_items import PackError, PackItem, admit
from fno.models import IST
from fno.playbook.registry import RegistryRow

from .builders import (
    CUTOFF,
    DAY,
    SNAPSHOT,
    FixedPlaybook,
    approved,
    builder,
    event_row,
    opportunity_set,
    snapshot_folder,
)  # fmt: skip
from .test_common_pack import LeakyInput

SATURDAY = date(2026, 10, 17)


def rows_for(strategy, *changes):
    evidence = {"paper": "abcdef1"}
    return [
        RegistryRow(strategy.name, 1, strategy.parameters_sha256, status, on, "owner", evidence.get(status, ""))
        for status, on in changes
    ]


def test_only_versions_paper_at_the_start_of_the_day_are_offered(tmp_path):
    """Must-fix 1: a registered research version, a version approved then paused, and a version approved on the day
    are not offered; the version approved before the day is (plants P6 and P14 must fail this)."""
    good, _ = approved("sc-good")
    candidate, _ = approved("sc-candidate")
    stopped, _ = approved("sc-stopped")
    today, _ = approved("sc-today")
    week = DAY - timedelta(days=7)
    rows = (
        rows_for(good, ("paper", week))
        + rows_for(candidate, ("research", week))
        + rows_for(stopped, ("paper", week), ("paused", DAY - timedelta(days=1)))
        + rows_for(today, ("research", week), ("paper", DAY))
    )
    snapshot_folder(tmp_path)
    pack = builder(tmp_path, playbook=FixedPlaybook([good, candidate, stopped, today], rows)).build(DAY, CUTOFF)
    assert [o["opportunity_id"] for o in pack.body["opportunities"]] == ["sc-good-v1:2026-11-23", "no_trade"]


def late_and_untimed(tmp_path, vix_time):
    folder = snapshot_folder(tmp_path)
    csv_path, meta_path = folder / f"{SNAPSHOT}.csv", folder / f"{SNAPSHOT}.meta.json"
    rows = csv_path.read_text().splitlines()
    slow = (
        rows[-1]
        .replace(
            "2026-10-13T14:57:20+05:30,2026-10-13T14:57:20+05:30", "2026-10-13T14:59:59+05:30,2026-10-13T15:00:01+05:30"
        )
        .replace(",22450,PE,", ",22500,PE,")
    )
    csv_path.write_text("\n".join([*rows, slow]) + "\n")  # fmt: skip
    meta = json.loads(meta_path.read_text())
    meta["india_vix_time"] = vix_time
    meta_path.write_text(json.dumps(meta))
    return builder(tmp_path).build(DAY, CUTOFF)


@pytest.mark.parametrize("vix_time", ["", "soon"])
def test_a_quote_received_after_15_00_and_an_untimed_vix_are_refused(tmp_path, vix_time):
    """Must-fix 2: a request sent at 14:59:59 whose response arrived at 15:00:01 is late (P3); VIX without a readable
    NSE time is untimed, never admitted at the capture's time (P4)."""
    refused = {r["name"]: r["reason"] for r in late_and_untimed(tmp_path, vix_time).body["refused"]}
    assert refused == {"option:2026-11-23:22500:PE": "after the cutoff", "india_vix": "no availability time"}


def test_an_item_at_exactly_the_cutoff_is_kept():
    """Must-fix 2 (P1): available at 15:00:00 is not after 15:00."""
    cutoff = datetime(2026, 10, 13, 15, 0, tzinfo=IST)
    items, refused = admit([PackItem("edge", 1, "test", "2026-10-13T15:00:00+05:30")], cutoff)
    assert [i.name for i in items] == ["edge"] and refused == ()


def test_a_session_day_without_its_snapshot_is_refused_and_a_closed_day_is_packed(tmp_path):
    """Must-fix 3: no empty pack is frozen for a session day; a closed day still gets its session-only pack."""
    with pytest.raises(PackError, match="no canonical A4 snapshot for 2026-10-13"):
        builder(tmp_path).build(DAY, CUTOFF)
    closed = builder(tmp_path).build(SATURDAY, CUTOFF)
    assert closed.body["provenance"]["a4_snapshot"]["snapshot_id"] is None


def test_two_items_with_one_name_are_refused():
    twins = [PackItem("x", 1, "a", "2026-10-13T10:00:00+05:30"), PackItem("x", 2, "b", "2026-10-13T10:00:00+05:30")]
    with pytest.raises(PackError, match="share a name"):
        admit(twins, datetime(2026, 10, 13, 15, 0, tzinfo=IST))


def test_past_events_are_not_offered(tmp_path):
    events = event_row("2026-10-09", "2026-09-01") + event_row("2026-12-05", "2026-10-01")
    snapshot_folder(tmp_path)
    names = {i["name"] for i in builder(tmp_path, events=events).build(DAY, CUTOFF).body["items"]}
    assert "event:2026-12-05:rbi_policy" in names and "event:2026-10-09:rbi_policy" not in names


def test_the_last_260_closes_before_the_day_are_kept(tmp_path):
    days = [DAY - timedelta(days=n) for n in range(300, 0, -1)]
    snapshot_folder(tmp_path)
    closes = [
        i["name"]
        for i in builder(tmp_path, closes_days=days).build(DAY, CUTOFF).body["items"]
        if i["name"].startswith("close:")
    ]
    assert len(closes) == 260 and closes[0] == f"close:{days[40].isoformat()}" and closes[-1] == "close:2026-10-12"


def test_a_journal_path_alone_is_refused():
    with pytest.raises(PackError, match="market data only"):
        CommonPackBuilder((LeakyInput("see journal/packs"),), opportunity_set(), FixedPlaybook()).build(DAY, CUTOFF)


def test_the_provenance_names_the_snapshot_files_by_hash(tmp_path):
    folder = snapshot_folder(tmp_path)
    provenance = builder(tmp_path).build(DAY, CUTOFF).body["provenance"]["a4_snapshot"]
    for suffix, key in ((".csv", "csv_sha256"), (".meta.json", "meta_sha256")):
        assert provenance[key] == hashlib.sha256((folder / f"{SNAPSHOT}{suffix}").read_bytes()).hexdigest()

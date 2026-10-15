"""Story E2's common market pack: no book data (1), byte-identical rebuilds (3), refusal after the cutoff by name (4)
and the common opportunity set against a hand computation (5)."""

import json
from datetime import date

import pytest

from fno.desk.common_pack import CommonPackBuilder, require_market_only
from fno.desk.pack_inputs import CommonInput, InputBatch
from fno.desk.pack_items import PackError, PackItem

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
)

TOP_KEYS = {"schema_version", "kind", "day", "cutoff", "provenance", "items", "refused", "opportunities"}


def build(root, **kwargs):
    snapshot_folder(root)
    return builder(root, **kwargs).build(DAY, CUTOFF)


def test_the_pack_holds_market_items_with_source_and_time(tmp_path):
    pack = build(tmp_path)
    assert set(pack.body) == TOP_KEYS
    names = {item["name"] for item in pack.body["items"]}
    assert {"india_vix", "session", "future:2026-10-27", "future:2026-11-23", "close:2026-10-12"} <= names
    assert {"spot:2026-10-27", "spot:2026-11-23", "quote_counts"} <= names  # story E2b: no per-contract quotes
    assert not any(name.startswith("option:") for name in names) and pack.body["schema_version"] == 2
    assert all(item["source"] and item["available_at"] for item in pack.body["items"])
    assert pack.body["provenance"]["a4_snapshot"]["snapshot_id"] == SNAPSHOT


def test_a_planted_position_never_reaches_the_common_pack(tmp_path):
    planted = tmp_path / "journal" / "book1_rules" / "account" / "positions.json"
    planted.parent.mkdir(parents=True)
    planted.write_text('{"PLANTED-POSITION-7Q": 1}')
    data = build(tmp_path).data.decode()
    assert "PLANTED-POSITION-7Q" not in data and "journal/" not in data and "book1_rules" not in data


class LeakyInput(CommonInput):
    name = "leaky"

    def __init__(self, value, available_at="2026-10-13T10:00:00+05:30"):
        self.value, self.available_at = value, available_at

    def collect(self, day):
        return InputBatch((PackItem("leak", self.value, "test", self.available_at),))


@pytest.mark.parametrize("value", ["book2_hybrid account", "journal/book3_ai/decisions/x.json"])
def test_a_pack_naming_a_book_or_journal_path_is_refused(value):
    with pytest.raises(PackError, match="market data only"):
        CommonPackBuilder((LeakyInput(value),), opportunity_set(), FixedPlaybook()).build(DAY, CUTOFF)


def test_require_market_only_accepts_market_text():
    require_market_only(b'{"name": "option:2026-11-23:22450:CE"}')


def test_building_twice_gives_byte_identical_packs(tmp_path):
    snapshot_folder(tmp_path)
    first, second = builder(tmp_path).build(DAY, CUTOFF), builder(tmp_path).build(DAY, CUTOFF)
    assert first.data == second.data and first.sha256 == second.sha256


def test_later_closes_and_announcements_do_not_change_a_rebuilt_pack(tmp_path):
    snapshot_folder(tmp_path)
    original = builder(tmp_path, events=event_row("2026-12-05", "2026-10-01")).build(DAY, CUTOFF)
    later = builder(
        tmp_path,
        events=event_row("2026-12-05", "2026-10-01") + event_row("2027-02-01", "2026-10-20", "budget"),
        closes_days=(date(2026, 10, 9), date(2026, 10, 12), date(2026, 10, 13), date(2026, 10, 14)),
    ).build(DAY, CUTOFF)
    assert later.data == original.data


def test_an_input_after_the_cutoff_is_refused_by_name(tmp_path):
    late = LeakyInput(1.0, available_at="2026-10-13T15:00:01+05:30")
    pack = CommonPackBuilder((late,), opportunity_set(), FixedPlaybook()).build(DAY, CUTOFF)
    assert pack.body["items"] == []
    assert pack.body["refused"] == [
        {"name": "leak", "available_at": "2026-10-13T15:00:01+05:30", "reason": "after the cutoff"}
    ]


def test_a_quote_and_vix_observed_after_15_00_are_refused_by_name(tmp_path):
    folder = snapshot_folder(tmp_path)
    csv_path, meta_path = folder / f"{SNAPSHOT}.csv", folder / f"{SNAPSHOT}.meta.json"
    rows = csv_path.read_text().splitlines()
    late = (
        rows[-1].replace("2026-10-13T14:57:20+05:30", "2026-10-13T15:03:00+05:30").replace(",22450,PE,", ",22500,PE,")
    )
    csv_path.write_text("\n".join([*rows, late]) + "\n")
    meta = json.loads(meta_path.read_text())
    meta["india_vix_time"] = "13-Oct-2026 15:02"
    meta_path.write_text(json.dumps(meta))
    pack = builder(tmp_path).build(DAY, CUTOFF)
    refused = {r["name"]: r["reason"] for r in pack.body["refused"]}
    # story E2b: a late row makes the capture's counts late; each chain's spot was known with its first row
    assert refused == {"quote_counts": "after the cutoff", "india_vix": "after the cutoff"}
    assert {"spot:2026-10-27", "spot:2026-11-23"} <= {i["name"] for i in pack.body["items"]}
    assert "india_vix" not in {i["name"] for i in pack.body["items"]}


def test_an_event_announced_on_the_day_is_refused_one_announced_before_is_kept(tmp_path):
    events = event_row("2026-12-05", "2026-10-12") + event_row("2027-02-01", "2026-10-13", "budget")
    pack = build(tmp_path, events=events)
    assert "event:2026-12-05:rbi_policy" in {i["name"] for i in pack.body["items"]}
    assert [r["name"] for r in pack.body["refused"]] == ["event:2027-02-01:budget"]


def test_the_opportunity_set_matches_a_hand_computation(tmp_path):
    """13 Oct 2026: monthly futures expire 27 Oct (14 days) and 23 Nov (41 days; 42 on 12 Oct). A 30-41 day window
    opens on 13 Oct for 23 Nov; exit = last session on or before 2 Nov (23 Nov - 21 days) = Monday 2 Nov. A 30-45 day
    window opened earlier (no opportunity today); a version approved today counts from tomorrow."""
    fresh, fresh_row = approved("sc-fresh")
    early, early_row = approved("sc-early", max_days=45)
    today, today_row = approved("sc-today", on=DAY)
    playbook = FixedPlaybook([fresh, early, today], [fresh_row, early_row, today_row])
    pack = build(tmp_path, playbook=playbook)
    assert pack.body["opportunities"] == [
        {"opportunity_id": "sc-fresh-v1:2026-11-23", "strategy": "sc-fresh", "version": 1,
         "rule_sha256": fresh.parameters_sha256, "expiry": "2026-11-23", "entry_day": "2026-10-13",
         "exit_day": "2026-11-02"},
        {"opportunity_id": "no_trade"},
    ]  # fmt: skip


def test_nothing_approved_leaves_only_no_trade(tmp_path):
    assert build(tmp_path).body["opportunities"] == [{"opportunity_id": "no_trade"}]

"""The app's pack builders on the repository itself. No A4 snapshot is committed yet, so a session day is refused and
a closed day builds from the committed inputs, with no book data; Book 1's private pack reads only its own account and
the playbook."""

from datetime import date

import pytest

from fno.composition import DESK_DECISION_TIME
from fno.desk.pack_items import PackError
from fno.desk.pack_wiring import build_common_pack_builder, build_private_pack_builder

DAY = date(2026, 10, 13)
SATURDAY = date(2026, 10, 17)


def test_the_app_refuses_a_session_day_without_its_snapshot():
    """No A4 snapshot is committed for 13 Oct 2026, a regular session: nothing may be frozen for it (judge 72)."""
    with pytest.raises(PackError, match="no canonical A4 snapshot for 2026-10-13"):
        build_common_pack_builder().build(DAY, DESK_DECISION_TIME)


def test_the_app_common_pack_builds_for_a_closed_day_and_names_its_inputs():
    pack = build_common_pack_builder().build(SATURDAY, DESK_DECISION_TIME)
    assert set(pack.body["provenance"]) == {"a4_snapshot", "daily_closes", "events", "session"}
    assert pack.body["opportunities"][-1] == {"opportunity_id": "no_trade"}
    assert "close:2026-10-12" in {item["name"] for item in pack.body["items"]}


def test_book_1_private_pack_reads_only_its_folders():
    paths = [f["path"] for f in build_private_pack_builder().build("book1_rules", DAY).body["files"]]
    assert paths and all(p.startswith(("journal/book1_rules/", "playbook/")) for p in paths)

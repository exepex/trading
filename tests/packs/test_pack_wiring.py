"""The app's pack builders on the repository itself: the common pack builds from the committed inputs (no snapshot is
committed for this day, which the provenance says) and holds no book data; Book 1's private pack reads only its own
account and the playbook."""

from datetime import date

from fno.composition import DESK_DECISION_TIME
from fno.desk.pack_wiring import build_common_pack_builder, build_private_pack_builder

DAY = date(2026, 10, 13)


def test_the_app_common_pack_builds_and_names_its_inputs():
    pack = build_common_pack_builder().build(DAY, DESK_DECISION_TIME)
    assert set(pack.body["provenance"]) == {"a4_snapshot", "daily_closes", "events", "session"}
    assert pack.body["opportunities"][-1] == {"opportunity_id": "no_trade"}
    assert "close:2026-10-12" in {item["name"] for item in pack.body["items"]}


def test_book_1_private_pack_reads_only_its_folders():
    paths = [f["path"] for f in build_private_pack_builder().build("book1_rules", DAY).body["files"]]
    assert paths and all(p.startswith(("journal/book1_rules/", "playbook/")) for p in paths)

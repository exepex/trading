"""Story A19 criteria 4, 5 and 6: dedup and versions, write-once storage through O9, memory across restarts."""

import json
from datetime import timedelta

import pytest

from fno.news.memory import SeenMemory
from fno.news.parse import NewsItem
from fno.news.store import NewsStore, SeenSetLoadError
from fno.news.times import PublishedTime
from fno.storage.data_store import DataStore
from fno.storage.drive_cache import DriveCache
from fno.storage.receipts import ReceiptFolder
from tests.news.fakes import HEADLINE, LINK, MARKETS, MINT, ist
from tests.quotes.drive_fakes import FakeDrive

T0 = ist(2026, 10, 16, 10, 0)


def item(title=HEADLINE, url=LINK, summary="s", raw="Fri, 16 Oct 2026 09:00:00 +0530", value=None, precision=None):
    value = value if value is not None else "2026-10-16T03:30:00+00:00"
    return NewsItem(title, url, summary, PublishedTime(raw, value, precision or "second"))


def test_same_url_across_feeds_and_polls_is_one_item_with_tracking_ignored():
    memory = SeenMemory()
    assert len(memory.observe(MARKETS, [item()], T0, False)) == 1
    assert memory.observe(MARKETS, [item()], T0 + timedelta(minutes=5), False) == []
    assert memory.observe(MINT, [item(url=LINK + "?utm_source=rss")], T0, False) == []


def test_a_changed_title_is_a_new_version_and_the_first_is_kept():
    memory = SeenMemory()
    [first] = memory.observe(MARKETS, [item()], T0, False)
    [second] = memory.observe(MARKETS, [item(title="Fixture headline revised")], T0 + timedelta(minutes=5), False)
    assert first["item_id"] == second["item_id"] and first["version"] != second["version"]
    assert (first["new_item"], second["new_item"]) == (True, False)
    assert len(memory.versions[first["item_id"]]) == 2


@pytest.mark.parametrize("after, linked", [(timedelta(hours=24), True), (timedelta(hours=24, seconds=1), False)])
def test_same_headline_from_another_publisher_is_linked_within_24_hours(after, linked):
    memory = SeenMemory()
    [first] = memory.observe(MARKETS, [item()], T0, False)
    [other] = memory.observe(MINT, [item(title=HEADLINE.upper() + "!", url=LINK + "-mint")], T0 + after, False)
    assert other["same_headline_as"] == (first["item_id"] if linked else None)


def test_same_headline_from_the_same_publisher_is_not_linked():
    memory = SeenMemory()
    memory.observe(MARKETS, [item()], T0, False)
    [other] = memory.observe(MARKETS, [item(url=LINK + "-b")], T0, False)
    assert other["same_headline_as"] is None


@pytest.mark.parametrize(
    "age, flagged", [(timedelta(days=13), False), (timedelta(days=13, minutes=1), True), (timedelta(days=2), False)]
)
def test_an_unseen_item_older_than_13_days_is_flagged(age, flagged):
    published = (T0 - age).isoformat()
    [record] = SeenMemory().observe(MARKETS, [item(value=published)], T0, False)
    assert record["beyond_window"] is flagged


@pytest.mark.parametrize("days, flagged", [(13, False), (14, True)])
def test_a_date_only_item_is_compared_by_day(days, flagged):
    day = (T0 - timedelta(days=days)).date().isoformat()
    [record] = SeenMemory().observe(MARKETS, [item(value=day, precision="day")], T0, False)
    assert record["beyond_window"] is flagged


def test_a_feeds_first_poll_marks_bootstrap_and_never_beyond_window():
    old = (T0 - timedelta(days=40)).isoformat()
    [record] = SeenMemory().observe(MARKETS, [item(value=old)], T0, True)
    assert (record["bootstrap"], record["beyond_window"]) == (True, False)


def test_prune_forgets_only_items_older_than_14_days():
    memory = SeenMemory()
    memory.observe(MARKETS, [item(url=LINK + "-old")], T0 - timedelta(days=14, minutes=1), False)
    memory.observe(MARKETS, [item(url=LINK + "-edge")], T0 - timedelta(days=14), False)
    memory.prune(T0)
    assert len(memory.versions) == 1


def store(tmp_path, drive=None, run_id="20261016T043000Z-aaaaaa"):
    drive = drive or FakeDrive()
    receipts = ReceiptFolder(tmp_path / "receipts")
    data = DataStore(drive, "data", receipts, "news-capture", run_id, clock=lambda: T0)
    return NewsStore(data, receipts, DriveCache(drive, receipts, tmp_path / "cache")), drive


def poll_line(at):
    return {"line": "poll", "polled_at": at.isoformat(), "run_id": "r",
            "feeds": {"et-markets": {"outcome": "nothing_new", "listed": 1, "new": 0}}}  # fmt: skip


def item_line(record, at, feed=MARKETS):
    return {"line": "item", **record, "feed": feed.id, "publisher": feed.publisher, "title": HEADLINE,
            "first_seen_at": at.isoformat()}  # fmt: skip


@pytest.mark.parametrize("age", [timedelta(days=2, minutes=1), timedelta(days=9)])
def test_a_restart_never_stores_a_known_item_again(tmp_path, age):
    seen_at = T0 - age
    first, _ = store(tmp_path)
    memory = SeenMemory()
    [record] = memory.observe(MARKETS, [item()], seen_at, True)
    first.put_snapshot(seen_at, 1, memory)
    later = item_line(memory.observe(MARKETS, [item(url=LINK + "-later")], seen_at, False)[0], seen_at)
    first.put_part(seen_at + timedelta(minutes=1), 2, [poll_line(seen_at), later])
    restarted, _ = store(tmp_path, first.data.drive, run_id="20261016T050000Z-bbbbbb")
    restarted.data.clock = lambda: T0 + timedelta(seconds=1)  # the part's receipt is newer than the snapshot's
    loaded = restarted.load_memory()
    assert loaded.observe(MARKETS, [item(), item(url=LINK + "-later")], T0, False) == []
    assert loaded.last_heartbeat == seen_at.isoformat()


def test_parts_after_the_snapshot_are_replayed(tmp_path):
    news, drive = store(tmp_path)
    news.put_snapshot(T0, 1, SeenMemory())
    news.data.clock = lambda: T0 + timedelta(minutes=15)
    record = SeenMemory().observe(MARKETS, [item()], T0 + timedelta(minutes=10), False)[0]
    news.put_part(T0 + timedelta(minutes=15), 2, [poll_line(T0 + timedelta(minutes=10)), item_line(record, T0)])
    loaded = news.load_memory()
    assert record["item_id"] in loaded.versions
    assert loaded.last_poll["et-markets"] == (T0 + timedelta(minutes=10)).isoformat()


def test_no_news_records_means_no_load(tmp_path):
    news, _ = store(tmp_path)
    assert not news.has_records()


def test_receipts_without_readable_files_stop_the_load(tmp_path):
    news, drive = store(tmp_path)
    news.put_snapshot(T0, 1, SeenMemory())
    drive.files.clear()  # Drive lost the file the receipt names
    with pytest.raises(SeenSetLoadError):
        news.load_memory()


def test_parts_go_to_drive_with_a_receipt_and_nothing_else(tmp_path):
    news, drive = store(tmp_path)
    receipt = news.put_part(T0, 3, [poll_line(T0)])
    assert receipt.path == "data/news/parts/2026/10/16/20261016T043000Z-aaaaaa-0003.jsonl"
    assert json.loads(drive.files[receipt.path])["line"] == "poll"
    written = [p for p in tmp_path.rglob("*") if p.is_file()]
    assert all(HEADLINE not in p.read_text(errors="ignore") for p in written if "receipts" in p.parts)

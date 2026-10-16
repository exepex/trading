"""Story A19 criteria 5 and 6 end to end: two runs through FeedPoller, NewsRun and NewsStore on a fake Drive. The
second run's memory, rebuilt from the snapshot and the later parts, equals the first run's live memory; nothing
known is stored again; and no headline or link reaches the log, the alerts, the printed lines or the receipts."""

import json
from datetime import time, timedelta

from fno.news.episodes import Episodes
from fno.news.memory import SeenMemory
from fno.news.polling import FeedPoller
from fno.news.runner import NewsRun, RunPlan
from fno.news.settings import Window
from fno.news.stale import StaleRule
from fno.news.store import NewsStore
from fno.news.window import PollingWindow
from fno.storage.data_store import DataStore
from fno.storage.drive_cache import DriveCache
from fno.storage.receipts import ReceiptFolder
from tests.news.fakes import (
    HEADLINE,
    LINK,
    MARKETS,
    MINT,
    Alerts,
    Clock,
    Committer,
    MemoryLog,
    ScriptedSource,
    calendar,
    ist,
    item_xml,
    rss,
)
from tests.quotes.drive_fakes import FakeDrive

PUB = "Fri, 16 Oct 2026 09:59:00 +0530"
ET = rss(item_xml(HEADLINE, LINK, PUB), item_xml("Second fixture", LINK + "-2", PUB))
ET_REVISED = rss(item_xml(HEADLINE + " revised", LINK, PUB), item_xml("Second fixture", LINK + "-2", PUB))
MINT_FEED = rss(item_xml(HEADLINE, LINK + "-mint", PUB), item_xml("Second fixture", LINK + "-2?utm_source=x", PUB))


def one_run(tmp_path, drive, start, minutes, et_answers, run_id, log, alerts, printed):
    clock = Clock(start)
    receipts = ReceiptFolder(tmp_path / "receipts")
    store = NewsStore(DataStore(drive, "data", receipts, "news-capture", run_id, clock=clock), receipts,
                      DriveCache(drive, receipts, tmp_path / "cache"))  # fmt: skip
    memory = store.load_memory() if store.has_records() else SeenMemory()
    loaded = json.loads(json.dumps(memory.to_dict()))  # a copy: the run goes on changing the memory
    episodes = Episodes(log, alerts, clock, printed.append)
    sources = [ScriptedSource(MARKETS, et_answers, clock), ScriptedSource(MINT, [MINT_FEED], clock)]
    poller = FeedPoller(sources, memory, episodes, StaleRule(calendar()), run_id)
    plan = RunPlan(PollingWindow(Window(time(7), time(23))), False, timedelta(minutes=minutes))
    run = NewsRun(poller, memory, store, episodes, Committer(), plan, clock, clock.sleep, printed.append)
    run.run()
    lines = store.part_lines([r for r in receipts.under("data/news/parts") if run_id in r.path])
    return loaded, memory, [line for line in lines if line["line"] == "item"], tmp_path / "receipts"


def test_a_restart_rebuilds_the_live_memory_and_stores_nothing_known_again(tmp_path):
    drive, log, alerts, printed = FakeDrive(), MemoryLog(), Alerts(), []
    _, live, first_items, _ = one_run(tmp_path, drive, ist(2026, 10, 16, 10, 0), 140, [ET], "20261016T043000Z-aaaaaa",
                                      log, alerts, printed)  # fmt: skip
    assert len(first_items) == 3  # ET's two items and Mint's own link; Mint's tracked copy of item 2 is the same item
    assert first_items[2]["same_headline_as"] == first_items[0]["item_id"]
    loaded, _, second_items, receipts = one_run(tmp_path, drive, ist(2026, 10, 16, 12, 25), 20, [ET, ET_REVISED],
                                                "20261016T065500Z-bbbbbb", log, alerts, printed)  # fmt: skip
    assert loaded == live.to_dict()  # snapshot at 12:00 plus the part at 12:20 give the live memory exactly
    assert [(i["new_item"], i["title"]) for i in second_items] == [(False, HEADLINE + " revised")]
    assert second_items[0]["previous_poll_at"] == ist(2026, 10, 16, 12, 25).isoformat()  # its own first poll
    texts = [*log.messages, *alerts.sent, *printed]
    texts += [p.read_text() for p in receipts.rglob("*") if p.is_file()]
    assert all(HEADLINE not in text and LINK not in text for text in texts)

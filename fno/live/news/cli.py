"""`python -m fno live news-once` and `news-report`: check the news sources and see which is fastest."""

from __future__ import annotations

from datetime import datetime, timedelta

from ...constants import EVENT_NEWS_SIGHTING, EVENT_NEWS_STORY
from ..learning.news_speed import format_speed_report, source_speeds
from ..services import LiveServices, build_news_watcher

ONCE_ROW = "{name:<28} {status}"
HEADLINE_ROW = "    {when} {title}  [{symbols}]"
SHOWN_HEADLINES = 3
DISABLED = "News watcher is switched off (live.news.enabled in config.yaml)."


def news_once(services: LiveServices, now: datetime) -> int:
    """Ask every source once, one after another (with the usual gap), and show what each returned."""
    watcher = build_news_watcher(services)
    if watcher is None:
        print(DISABLED)
        return 1
    watcher.schedule.start(now)
    for plan in watcher.schedule.plans:
        try:
            items = plan.source.fetch(now)
        except Exception as exc:  # noqa: BLE001 - a diagnostic shows every failure and carries on
            print(ONCE_ROW.format(name=plan.name, status=f"FAILED: {exc}"))
            continue
        print(ONCE_ROW.format(name=plan.name, status=f"{len(items)} headlines"))
        for item in items[:SHOWN_HEADLINES]:
            when = item.published_at.strftime("%d %b %H:%M") if item.published_at else "--"
            symbols = ", ".join(watcher.book.tagger.symbols(item.title, item.symbols)) or "-"
            print(HEADLINE_ROW.format(when=when, title=item.title[:90], symbols=symbols))
    return 0


def news_report(services: LiveServices, now: datetime, days: int) -> int:
    since = (now - timedelta(days=days)).date()
    stories = services.store.payloads(EVENT_NEWS_STORY, since)
    sightings = services.store.payloads(EVENT_NEWS_SIGHTING, since)
    print(f"News sources over the last {days} days: {len(stories)} stories")
    print(format_speed_report(source_speeds(stories, sightings)))
    return 0

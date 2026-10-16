"""`python -m fno news ...` (story A19): `run` (the poller), `probe` (each feed from this machine: status, size,
count and newest time only, since run logs are public), `kick` (the starter), `list` and `quiet-spells` (readers)."""

from __future__ import annotations

import os
from datetime import timedelta

from .names import (
    CLOCK,
    COVERAGE_GAP,
    DISPATCH,
    DRIVE_WRITE,
    RECEIPT_COMMIT,
    RESTART_STOPPED,
    SEEN_SET_LOAD,
    SNAPSHOT_WRITE,
    START,
)

RUN_STEPS = frozenset(
    {CLOCK, COVERAGE_GAP, DISPATCH, DRIVE_WRITE, RECEIPT_COMMIT, RESTART_STOPPED, SEEN_SET_LOAD, SNAPSHOT_WRITE, START}
)
LOAD_TRIES, LOAD_PAUSE_SECONDS = 3, 60

PROBE_LINE = "{feed}: HTTP {status}, {size} bytes, {count} item(s), newest published {newest}"
PROBE_FAILED = "{feed}: FAILED {kind} ({detail})"
SUCCESSOR = "successor={value}"
RECORDED = "recorded=true"
START_STOP = "news run NOT started: the error log or alerts could not be built ({problem})"
LOAD_STOP = "news run stopped: {problem}"


def add_news_parser(sub) -> None:
    news = sub.add_parser("news", help="news and announcements with their first-seen time (story A19)")
    actions = news.add_subparsers(dest="news_action", required=True)
    run = actions.add_parser("run", help="poll the feeds every 5 minutes until the run's end (GitHub workflow)")
    run.add_argument("--max-minutes", type=int, default=330, help="stop after this many minutes (default 330)")
    run.set_defaults(func=cmd_run)
    actions.add_parser("probe", help="read each feed once and print status and counts only").set_defaults(
        func=cmd_probe
    )
    from .kick_cli import add_kick_parser
    from .read_cli import add_read_parsers

    add_kick_parser(actions)
    add_read_parsers(actions)


def cmd_run(args, out=print, parts=None) -> int:
    """0 after a run that saved and committed everything; 1 otherwise. Before any non-zero exit whose failure it
    already recorded and alerted, it writes `recorded=true`, so the workflow's generic alert stays quiet."""
    from .kick import wants_successor
    from .polling import FeedPoller
    from .runner import NewsRun, RunPlan

    if parts is None:
        built = _build_or_record(out)
        if built is None:
            return 1
        parts = built
    episodes = parts["episodes"]
    episodes.ok(START)
    episodes.ok(DISPATCH)  # a run started, so news-capture can be dispatched again
    memory = _load_memory(parts, out)
    if memory is None:
        return 1
    close_removed_feeds(episodes, {source.feed.id for source in parts["sources"]})
    poller = FeedPoller(parts["sources"], memory, episodes, parts["stale"], parts["run_id"])
    plan = RunPlan(parts["window"], parts["bridge"], timedelta(minutes=args.max_minutes))
    run = NewsRun(poller, memory, parts["store"], episodes, parts["committer"], plan, parts["clock"], parts["sleep"],
                  out)  # fmt: skip
    lasted = run.run()
    successor = wants_successor(lasted, parts["clock"](), parts["window"], parts["bridge"])
    _output(SUCCESSOR.format(value=str(successor).lower()), out)
    if not run.saved:
        _output(RECORDED, out)
        return 1
    return 0


def _build_or_record(out) -> dict | None:
    """The run's parts; when they cannot be built (settings, Drive credentials, the calendar), one `start` row and
    alert when the error log itself can be built, else a printed line for the workflow's alert."""
    from .wiring import build_committer, build_episodes

    try:
        episodes = build_episodes()
    except Exception as problem:
        out(START_STOP.format(problem=type(problem).__name__))
        return None
    try:
        return {**_real_parts(), "episodes": episodes}
    except Exception as problem:
        episodes.fail(START, START, f"run not built ({type(problem).__name__}: {str(problem)[:80]})")
        out(build_committer().commit("news capture: run not built"))
        _output(RECORDED, out)
        return None


def _load_memory(parts: dict, out):
    """The seen memory, tried `LOAD_TRIES` times (a Drive blip must not stop capture for hours); after the last try,
    one `seen_set_load` row and alert, and the run stops rather than store known items with false times."""
    from .memory import SeenMemory

    store, episodes = parts["store"], parts["episodes"]
    problem = None
    for attempt in range(LOAD_TRIES):
        if attempt:
            parts["sleep"](LOAD_PAUSE_SECONDS)
        try:
            memory = store.load_memory() if store.has_records() else SeenMemory()
        except Exception as error:  # unreadable records, Drive down: retried, then recorded
            problem = error
            continue
        episodes.ok(SEEN_SET_LOAD)
        return memory
    episodes.fail(SEEN_SET_LOAD, SEEN_SET_LOAD, f"seen set not loaded ({type(problem).__name__})")
    out(LOAD_STOP.format(problem=type(problem).__name__))
    out(parts["committer"].commit("news capture: seen set not loaded"))
    _output(RECORDED, out)
    return None


def close_removed_feeds(episodes, active: set[str]) -> None:
    """Closes episodes left open by a feed no longer read (removed, or switched off by `publisher_feeds`)."""
    for step in {step for step, _ in episodes.open if step not in RUN_STEPS and step not in active}:
        episodes.ok(step)


def cmd_probe(args, out=print, sources=None) -> int:
    from .parse import FeedProblem, parse_feed

    worst = 0
    for source in sources if sources is not None else _real_sources():
        try:
            fetch = source.fetch()
            items = parse_feed(fetch.data, source.feed)
        except FeedProblem as problem:
            out(PROBE_FAILED.format(feed=source.feed.id, kind=problem.kind, detail=problem))
            worst = 1
            continue
        dated = [i.published.value for i in items if i.published.value]
        out(PROBE_LINE.format(feed=source.feed.id, status=fetch.status, size=len(fetch.data), count=len(items),
                              newest=max(dated) if dated else "unknown"))  # fmt: skip
    return worst


def _output(line: str, out) -> None:
    """The successor flag for the workflow's next step (`GITHUB_OUTPUT`), and printed."""
    out(line)
    target = os.environ.get("GITHUB_OUTPUT")
    if target:
        with open(target, "a", encoding="utf-8") as fh:
            fh.write(line + "\n")


def _real_sources():
    from .wiring import build_settings, build_sources

    return build_sources(build_settings())


def _real_parts() -> dict:
    import time

    from ..storage.data_store import new_run_id
    from .wiring import (
        build_committer,
        build_settings,
        build_sources,
        build_stale_rule,
        build_store,
        build_window,
        now_utc,
    )

    settings, run_id = build_settings(), new_run_id()
    return {"sources": build_sources(settings), "store": build_store(run_id), "stale": build_stale_rule(),
            "window": build_window(settings), "bridge": settings.overnight_bridge, "committer": build_committer(),
            "clock": now_utc, "sleep": time.sleep, "run_id": run_id}  # fmt: skip

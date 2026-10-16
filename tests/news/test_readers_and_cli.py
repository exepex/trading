"""Story A19 criteria 5, 6, 9 and 12: the point-in-time reader, quiet spells, `news run`, `news probe` and the error
log adapter; no item text in anything printed."""

from argparse import Namespace
from datetime import date, time, timedelta

from fno.news.cli import cmd_probe, cmd_run
from fno.news.episodes import Episodes
from fno.news.error_log import CaptureEpisodeLog
from fno.news.memory import SeenMemory
from fno.news.read_cli import cmd_list, cmd_quiet_spells
from fno.news.reader import known_by
from fno.news.settings import Window
from fno.news.stale import StaleRule
from fno.news.store import SeenSetLoadError
from fno.news.window import PollingWindow
from tests.news.fakes import (
    HEADLINE,
    LINK,
    MARKETS,
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

T = ist(2026, 10, 19, 14, 30)


def line(key, seen, version="v1", feed="et-markets", title=HEADLINE):
    return {"line": "item", "item_id": key, "version": version, "feed": feed, "publisher": "P", "title": title,
            "url": LINK, "first_seen_at": seen.isoformat()}  # fmt: skip


def test_known_by_is_point_in_time():
    lines = [line("a", T - timedelta(hours=1)), line("a", T + timedelta(seconds=1), "v2"), line("b", T),
             line("c", T + timedelta(minutes=1)), {"line": "poll"}]  # fmt: skip
    found = known_by(lines, T)
    assert [(x["item_id"], x["version"]) for x in found] == [("a", "v1"), ("b", "v1")]
    later = known_by(lines, T + timedelta(minutes=1))
    assert ("a", "v2") in [(x["item_id"], x["version"]) for x in later]
    assert [x["item_id"] for x in known_by(lines, T + timedelta(minutes=1), since=T)] == ["b", "c"]


def test_list_prints_ist_times():
    printed = []
    cmd_list(Namespace(until="2026-10-19T14:30", since=None), printed.append, [line("b", T)])
    assert printed == [f"2026-10-19 14:30 | P | {HEADLINE} | {LINK}"]


def test_quiet_spells_by_day_type():
    moments = [(16, 10, 0), (16, 12, 30), (16, 20, 0), (17, 9, 0), (18, 21, 0)]
    lines = [line(str(n), ist(2026, 10, *m)) for n, m in enumerate(moments)]
    printed = []
    cmd_quiet_spells(None, printed.append, lines, StaleRule(calendar()))
    assert printed == ["et-markets: closed day: longest quiet spell 36.0 h",
                       "et-markets: session hours: longest quiet spell 7.5 h",
                       "et-markets: session night: longest quiet spell 13.0 h"]  # fmt: skip


class Store:
    def __init__(self, records=True, broken=False):
        self.records, self.broken, self.parts = records, broken, []

    def has_records(self):
        return self.records

    def load_memory(self):
        if self.broken:
            raise SeenSetLoadError("unreadable")
        return SeenMemory()

    def put_part(self, now, sequence, lines):
        self.parts.append(lines)

    def put_snapshot(self, now, sequence, memory):
        pass


def run_parts(store):
    clock, log, printed = Clock(ist(2026, 10, 16, 10, 0)), MemoryLog(), []
    feed = rss(item_xml(HEADLINE, LINK, "Fri, 16 Oct 2026 09:59:00 +0530"))
    parts = {"sources": [ScriptedSource(MARKETS, [feed], clock)], "store": store,
             "episodes": Episodes(log, Alerts(), clock, printed.append), "stale": StaleRule(calendar()),
             "window": PollingWindow(Window(time(7), time(23))), "bridge": False, "committer": Committer(),
             "clock": clock, "sleep": clock.sleep, "run_id": "r"}  # fmt: skip
    return parts, log, printed


def test_news_run_prints_counts_and_the_successor_flag_never_an_item(tmp_path, monkeypatch):
    output = tmp_path / "github_output"
    monkeypatch.setenv("GITHUB_OUTPUT", str(output))
    store = Store()
    parts, log, printed = run_parts(store)
    assert cmd_run(Namespace(max_minutes=30), printed.append, parts) == 0
    assert output.read_text() == "successor=true\n"
    assert store.parts and all(HEADLINE not in p and LINK not in p for p in printed)


def test_a_short_run_wants_no_successor(tmp_path, monkeypatch):
    monkeypatch.setenv("GITHUB_OUTPUT", str(tmp_path / "out"))
    parts, *_ = run_parts(Store())
    cmd_run(Namespace(max_minutes=9), lambda _: None, parts)
    assert (tmp_path / "out").read_text() == "successor=false\n"


def test_an_unreadable_seen_set_stops_the_run_with_one_row(monkeypatch):
    monkeypatch.delenv("GITHUB_OUTPUT", raising=False)
    store = Store(broken=True)
    parts, log, printed = run_parts(store)
    assert cmd_run(Namespace(max_minutes=30), printed.append, parts) == 1
    assert [r.kind for r in log.rows()] == ["seen_set_load"] and store.parts == []
    assert parts["committer"].calls == 1


def test_probe_prints_status_and_counts_only():
    clock, printed = Clock(T), []
    feed = rss(item_xml(HEADLINE, LINK, "Fri, 16 Oct 2026 09:59:00 +0530"))
    bad = ScriptedSource(MARKETS, [b"<html>Access Denied</html>"], clock)
    assert cmd_probe(None, printed.append, [ScriptedSource(MARKETS, [feed], clock), bad]) == 1
    assert (
        printed[0].startswith("et-markets: HTTP 200, ")
        and "1 item(s), newest published 2026-10-16T04:29:00" in printed[0]
    )
    assert printed[1].startswith("et-markets: FAILED not_xml")
    assert all(HEADLINE not in p and LINK not in p for p in printed)


class O10Log:
    """Stands in for O10's CaptureErrorLog (same rows() and append(CaptureError) shape)."""

    def __init__(self):
        self.appended = []

    def rows(self):
        return [Namespace(day=date(2026, 10, 16), job="news-capture", step="sebi", kind="stale")]

    def append(self, error):
        self.appended.append(error)


def test_error_log_adapter_writes_o10_rows():
    log = O10Log()
    adapter = CaptureEpisodeLog(log, lambda *fields: fields, "https://github.com/r/1")
    assert adapter.rows()[0].kind == "stale"
    adapter.append(date(2026, 10, 16), "sebi", "stale_recovered", "m")
    assert log.appended == [
        (date(2026, 10, 16), "news-capture", "sebi", "stale_recovered", "m", "https://github.com/r/1")
    ]

"""FL1-1c: the reasons' facts from the repository's own tables, A17's cue tables and P8's flows; a missing table
gives no fact."""

import gzip
from datetime import date, datetime

from fno.forecast_lab.design.renderer import DesignRenderer
from fno.forecast_lab.maker import ReportMaker
from fno.forecast_lab.page.builder import PageBuilder
from fno.forecast_lab.page.cues import FAILED
from fno.forecast_lab.page.facts import CueRows, RepositoryFacts

from .builders import REPORT_DAY, SESSIONS, Forecasts, at
from .test_maker_and_render import Camera, Pages
from .test_page_builder import History

DAY = date(2026, 10, 15)


def write(root, path, text, zipped=False):
    file = root / path
    file.parent.mkdir(parents=True, exist_ok=True)
    file.write_bytes(gzip.compress(text.encode()) if zipped else text.encode())


def test_every_table_is_read_up_to_the_day_and_a_missing_one_gives_nothing(tmp_path):
    write(
        tmp_path,
        "research/data/nifty-panel/warmup_closes.csv",
        "date,session,underlying,vix\n2026-10-14,regular,1,14.0\n2026-10-15,regular,1,15.5\n2026-10-16,regular,1,20\n",
    )
    write(tmp_path, "research/data/events/events.csv", "date,type\n2026-10-07,rbi_policy\n")
    write(
        tmp_path, "research/data/nifty-panel/options_2026.csv.gz", "date,expiry\n2026-10-01,2026-10-13\n", zipped=True
    )
    brent = Table([{"value_date": "2026-10-10", "value": "61.5"}, {"value_date": "2026-10-17", "value": "70"}])
    cues = CueRows(lambda: {"brent": brent, "usdinr_rbi": Table([])})
    source = RepositoryFacts(tmp_path, lambda day: {DAY: (-5000.0, 3000.0)}, cues)
    facts = source.facts(DAY)
    assert facts.vix == {date(2026, 10, 14): 14.0, DAY: 15.5}  # nothing after the day
    assert facts.events == {date(2026, 10, 7): "RBI policy decision"} and facts.expiries == {date(2026, 10, 13)}
    assert facts.brent == {date(2026, 10, 10): 61.5} and facts.usdinr == {}  # the cue rows up to the day only
    assert facts.flows == {DAY: (-5000.0, 3000.0)} and source.problems() == ()


class Table:
    def __init__(self, rows):
        self.held = rows

    def rows(self):
        return self.held


class Unreadable(Table):
    def rows(self):
        raise RuntimeError("data/global-cues/brent/x.csv: in the receipts, not returned by Drive")


def test_a_cue_table_drive_cannot_give_is_said_and_alerted_once_and_the_other_facts_stay(tmp_path):
    """O9b, agreed with FL1: a table that cannot be read gives no rows and is named (error type only, never the
    message), so the page shows one failed view in its system line and the report alerts it once."""
    cues = CueRows(
        lambda: {"brent": Unreadable([]), "usdinr_rbi": Table([{"value_date": "2026-10-14", "value": "88"}])}
    )
    source = RepositoryFacts(tmp_path, lambda day: {DAY: (-5000.0, 3000.0)}, cues)
    facts = source.facts(DAY)
    assert facts.brent == {} and facts.usdinr == {date(2026, 10, 14): 88.0} and facts.flows
    source.facts(DAY)  # read once: the second report day names it no second time
    assert source.problems() == ("brent: RuntimeError",)
    pages = PageBuilder(Forecasts(()), History(), source, SESSIONS, underlyings=("NIFTY",))
    view = pages.build(REPORT_DAY, at(REPORT_DAY, 15, 47))
    failed = [c for c in view.cues if c.status == FAILED]
    said = "Reasons' facts: brent: RuntimeError (that table's reasons are missing today)"
    assert [c.why for c in failed] == [said] and said in view.system and "receipts" not in said
    made = ReportMaker(Pages(view), DesignRenderer(), Camera()).make(REPORT_DAY, datetime.now(), "evening")
    assert made.alerts == (said,)


def test_the_wiring_reads_the_cue_tables_once_and_names_a_table_drive_cannot_give(monkeypatch):
    from fno.forecast_lab import page_wiring
    from fno.global_cues import wiring

    calls = []

    def unreadable(include_private):
        calls.append(include_private)
        raise RuntimeError("set the Drive settings to use the Drive data store")

    monkeypatch.setattr(wiring, "build_tables", unreadable)
    rows = page_wiring.cue_rows()
    assert rows("brent") == [] and rows("brent") == [] and rows.problems == ["brent: RuntimeError"]
    assert calls == [False]

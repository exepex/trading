"""FL1-1c: the reasons' facts from the repository's own tables, A17's cue tables and P8's flows; a missing table
gives no fact."""

import gzip
from datetime import date

from fno.forecast_lab.page.facts import RepositoryFacts

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
    cues = {"brent": [{"value_date": "2026-10-10", "value": "61.5"}, {"value_date": "2026-10-17", "value": "70"}]}
    facts = RepositoryFacts(tmp_path, lambda day: {DAY: (-5000.0, 3000.0)}, lambda cue: cues.get(cue, [])).facts(DAY)
    assert facts.vix == {date(2026, 10, 14): 14.0, DAY: 15.5}  # nothing after the day
    assert facts.events == {date(2026, 10, 7): "RBI policy decision"} and facts.expiries == {date(2026, 10, 13)}
    assert facts.brent == {date(2026, 10, 10): 61.5} and facts.usdinr == {}  # the cue rows up to the day only
    assert facts.flows == {DAY: (-5000.0, 3000.0)}


def test_a_cue_table_drive_cannot_give_reads_as_no_rows_and_is_read_once(monkeypatch):
    """O9b: the cue tables are in Drive; a missing setting or an unverified copy gives no fact, never a failed page."""
    from fno.forecast_lab import page_wiring
    from fno.global_cues import wiring

    calls = []

    def unreadable(include_private):
        calls.append(include_private)
        raise RuntimeError("set the Drive settings to use the Drive data store")

    monkeypatch.setattr(wiring, "build_tables", unreadable)
    rows = page_wiring.cue_rows()
    assert rows("brent") == [] and rows("brent") == [] and calls == [False]

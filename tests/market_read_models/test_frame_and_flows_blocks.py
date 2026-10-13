"""Contract 2.5 (owner, 14 Oct 2026: India's band, expiries and flows move to publisher fno): the `session`, `indices`,
`fno_events` (story P10) and `flows` (story P8) pages, built from NSE's calendar, P6's index rows, the NIFTY expiries
NSE lists and the archived flows copies; validated against the pinned 2.5 schemas."""

from dataclasses import replace
from datetime import date
from hashlib import sha256
from pathlib import Path

import pytest

from fno.market_read_models.flows_block import FlowsBlock, FlowsCopy
from fno.market_read_models.frame_blocks import FnoEventsBlock, IndicesIndiaBlock, SessionIndiaBlock
from fno.market_read_models.frame_inputs import FlowsReader, FrameInputs, frame_inputs
from fno.market_read_models.home_blocks import FiguresNotComputed
from fno.market_read_models.publication_inputs import PublicationInputsFile, copies_sha256
from fno.storage.raw_store import LocalFolderStore
from fno.storage.snapshot_source import FiiDiiCashSource, NsdlFpiDailySource
from fno.storage.wiring import build_session_calendar

from .test_market_contract_and_run import CONTRACT, DAY, Rows, builder, example_rows, run

FIXTURES = Path(__file__).parents[1] / "fixtures" / "flows"
CALENDAR = build_session_calendar()


def test_the_session_is_the_next_one_with_nses_hours_and_the_next_mornings_run():
    session = SessionIndiaBlock().build(example_rows())
    assert session == {
        "exchange": "India (NSE)", "zone": "IST", "session_date": "2026-10-13", "open_utc": "2026-10-13T03:45:00Z",
        "close_utc": "2026-10-13T10:00:00Z", "next_open_utc": "2026-10-13T03:45:00Z", "regime": None,
        "post_close_at": "2026-10-14T01:40:00Z", "major_event_names": [],  # 13 Oct: a weekly expiry, not major
    }  # fmt: skip
    friday = frame_inputs(CALENDAR, date(2026, 10, 9))
    assert friday == FrameInputs(date(2026, 10, 12), "regular")  # Friday's next session: Monday


def test_a_monthly_expiry_session_names_it_and_a_muhurat_session_is_not_guessed():
    rows = replace(example_rows(), frame=FrameInputs(date(2026, 10, 27), "regular"))
    assert SessionIndiaBlock().build(rows)["major_event_names"] == ["NSE monthly F&O expiry (last Tuesday)"]
    with pytest.raises(FiguresNotComputed, match="muhurat"):
        SessionIndiaBlock().build(replace(example_rows(), frame=FrameInputs(date(2026, 11, 8), "muhurat")))


def test_an_unknown_muhurat_session_leaves_out_only_the_session_page_and_the_run_publishes(tmp_path):
    """The real calendar row: 8 Nov 2026, muhurat, "timings circular not yet issued"; the session after Friday 6 Nov."""
    frame = frame_inputs(CALENDAR, date(2026, 11, 6))
    assert frame == FrameInputs(date(2026, 11, 8), "muhurat")
    rows = replace(example_rows(), frame=frame)
    assert SessionIndiaBlock().pages(rows) == {}
    market, alerts, publisher = run(tmp_path, Rows(rows))
    code, lines = market.run(DAY)
    assert code == 0 and alerts.sent == [] and "session" not in publisher.current()
    assert {"indices", "fno_events", "flows", "risk", "today", "chain_expiries"} <= set(publisher.current())


def test_the_indices_are_nifty_and_india_vix_at_the_close():
    indices = IndicesIndiaBlock().build(example_rows())["indices"]
    assert [(i["id"], i["last"], i["chg_pct"], i["chg_5d_pct"], i["as_of"], i["source"]) for i in indices] == [
        ("NIFTY50", 22363.35, -0.7, -0.85, "2026-10-12T10:00:00Z", "close"),
        ("INDIAVIX", 15.25, 6.05, 3.18, "2026-10-12T10:00:00Z", "close"),
    ]  # fmt: skip
    without_vix = replace(example_rows(), indices=[r for r in example_rows().indices if r["name"] != "India VIX"])
    with pytest.raises(FiguresNotComputed, match="never published with a made-up level"):
        IndicesIndiaBlock().build(without_vix)


def test_the_expiries_are_the_ones_nse_lists_and_their_first_four_equal_the_contracts_calendar():
    events = FnoEventsBlock().build(example_rows())["events"]
    assert [(e["date"], e["kind"], e["major"]) for e in events] == [
        ("2026-10-13", "weekly_expiry", False), ("2026-10-19", "weekly_expiry", False),
        ("2026-10-27", "fno_expiry", True), ("2026-11-03", "weekly_expiry", False),
        ("2026-11-09", "weekly_expiry", False), ("2026-11-23", "fno_expiry", True), ("2026-12-29", "fno_expiry", True),
    ]  # fmt: skip
    assert events[5]["title"] == "NSE monthly F&O expiry (moved for a holiday)"  # 23 Nov 2026 is a Monday
    example = CONTRACT.examples()["getFnoEvents_india_calendar"]["value"]["payload"]["events"]
    assert events[:4] == example  # the contract's calendar shows the first four (its horizon ends on 3 Nov)


def copies(tmp_path, by_fetch_day: dict[date, tuple[bytes, bytes]]) -> FlowsReader:
    store = LocalFolderStore(tmp_path)
    for fetched, (cash, nsdl) in by_fetch_day.items():
        store.put(FiiDiiCashSource.path_for(fetched), cash)
        store.put(NsdlFpiDailySource.path_for(fetched), nsdl)
    return FlowsReader(store, CALENDAR)


def test_flows_read_only_copies_filed_by_the_session_itself_never_a_later_one(tmp_path, monkeypatch):
    """Judge 66: session D publishes at 07:10 IST the next morning, so a copy filed the next day (here NSE's revised
    13 Oct values, filed 14 Oct) may be newer than the publication and is never read for D: widening the window by
    one session (or one day) breaks this test. Read for 14 Oct, the revision is the latest copy of 13 Oct and wins."""
    for source in (FiiDiiCashSource, NsdlFpiDailySource):
        monkeypatch.setattr(source, "first_day", date(2026, 10, 13))
    cash, nsdl = (
        (FIXTURES / "fii-dii-cash_13102026.json").read_bytes(),
        (FIXTURES / "fpi-daily-latest_13102026.html").read_bytes(),
    )
    revised = cash.replace(b"-1305.13", b"-1300.00")  # NSE's later version of 13 Oct's values
    later = cash.replace(b"13-Oct-2026", b"14-Oct-2026")  # the next session's values
    reader = copies(tmp_path, {
        date(2026, 10, 13): (cash, nsdl), date(2026, 10, 14): (revised, nsdl), date(2026, 10, 15): (later, nsdl),
    })  # fmt: skip
    assert reader.on(date(2026, 10, 12)).cash == []  # no copy filed by 12 Oct
    on_13 = reader.on(date(2026, 10, 13))
    assert [(c.day, c.fii.net) for c in on_13.cash] == [(date(2026, 10, 13), -1305.13)]  # 14 Oct's revision unread
    assert [(c.dataset, c.session, c.filed_on, c.sha256) for c in on_13.copies] == [
        ("nse/flows/fii-dii-cash", date(2026, 10, 13), date(2026, 10, 13), sha256(cash).hexdigest()),
        ("nsdl/fpi/fpi-daily", date(2026, 10, 13), date(2026, 10, 13), sha256(nsdl).hexdigest()),
    ]  # fmt: skip
    on_14 = reader.on(date(2026, 10, 14))  # 15 Oct's copy (14 Oct's values) is filed after 14 Oct: unread
    assert [(c.day, c.fii.net) for c in on_14.cash] == [(date(2026, 10, 13), -1300.0)]
    assert on_14.copies[0].filed_on == date(2026, 10, 14) and on_14.copies[0].sha256 == sha256(revised).hexdigest()
    block = FlowsBlock().build(replace(example_rows(), day=date(2026, 10, 13), flows=on_13))
    assert block["days"] == [{"date": "2026-10-13", "fii": {"buy": 13465.39, "sell": 14770.52, "net": -1305.13,
                              "provisional": True}, "dii": {"buy": 16232.97, "sell": 13793.73, "net": 2439.24,
                              "provisional": True}}]  # fmt: skip
    assert block["nsdl"] == [{"date": "2026-10-13", "net": 2000.73}]
    assert block["totals"]["d1"] == {"days_in_period": 1, "days": 1, "complete": True, "fii": -1305.13, "dii": 2439.24}
    assert block["totals"]["w1"] == {"days_in_period": 5, "days": 1, "complete": False, "fii": None, "dii": None}
    CONTRACT.validate("Flows", block)


def test_each_publication_records_the_copies_its_flows_read_once(tmp_path):
    copy = FlowsCopy("nse/flows/fii-dii-cash", date(2026, 10, 12), date(2026, 10, 12), "a" * 64)
    rows = replace(example_rows(), flows=replace(example_rows().flows, copies=[copy]))
    assert builder().build(rows).inputs == {"flows": [copy]}  # the other blocks read no alternative copies
    market, _, _ = run(tmp_path, Rows(rows))
    code, lines = market.run(DAY)
    listed = sha256(f"2026-10-12 2026-10-12 {'a' * 64}".encode()).hexdigest()
    assert code == 0 and copies_sha256([copy]) == listed
    line = f"    flows read 1 nse/flows/fii-dii-cash copies, newest filed 2026-10-12, list SHA-256 {listed}"
    assert line in lines and "publication inputs: 1 row(s) added to publication-inputs.csv" in lines
    publication_id = PublicationInputsFile(tmp_path / "publication-inputs.csv").rows()[0]["publication_id"]
    assert f"publication inputs: {publication_id} already recorded" in market.run(DAY)[1]  # a re-run adds nothing


def test_all_four_pages_validate_in_the_publication():
    records = builder().build(example_rows()).records
    assert {"session", "indices", "fno_events", "flows"} <= set(records)  # each validated as served on the way
    assert records["flows"]["payload"]["days"] == [] and records["flows"]["payload"]["totals"]["d1"]["days"] == 0

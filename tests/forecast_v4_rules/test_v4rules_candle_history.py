"""W8's one reader of A16b's candle history (story G7b completion; G14 imports it): each session's status,
`rv_session` (None when void), method, provenance and first-seen time; rows of another method or provenance are not
read; on the committed real table every row is read."""

from datetime import UTC, date, datetime

from fno.forecast_v4_rules.candle_history import W8_CANDLE_METHOD, CandleSession, candle_sessions
from fno.intraday.candle_rv_table import CandleRvTable
from fno.intraday.wiring import INTRADAY_FOLDER

SEEN = "2026-10-23T10:03:14+00:00"


def row(session, status="ok", rv="0.0001", method=W8_CANDLE_METHOD, provenance="backfilled"):
    return {"session": session, "status": status, "rv_session": rv, "method": method, "provenance": provenance,
            "first_seen_at": SEEN}  # fmt: skip


def test_each_session_carries_status_value_method_provenance_and_first_seen_time_in_session_order():
    found = candle_sessions([row("2026-10-22"), row("2026-10-21", status="void", rv="0.0002")])
    seen = datetime(2026, 10, 23, 10, 3, 14, tzinfo=UTC)
    assert found == [
        CandleSession(date(2026, 10, 21), "void", None, W8_CANDLE_METHOD, "backfilled", seen),
        CandleSession(date(2026, 10, 22), "ok", 0.0001, W8_CANDLE_METHOD, "backfilled", seen),
    ]


def test_rows_of_another_method_or_provenance_are_not_read():
    assert candle_sessions([row("2026-10-22", method="rv-quote-15m-v1"), row("2026-10-21", provenance="live")]) == []
    assert candle_sessions([]) == []


def test_the_committed_table_is_read_whole_and_its_void_rows_stay_void():
    rows = CandleRvTable(INTRADAY_FOLDER).rows()
    found = candle_sessions(rows)
    assert len(found) == len(rows) > 600  # A16b's 2024-2026 back-fill
    assert {s.day for s in found if s.rv_session is None} == {
        date.fromisoformat(r["session"]) for r in rows if r["status"] != "ok"
    }


def test_g14_reads_the_history_through_the_wiring_and_candle_rv_is_built_on_it(monkeypatch, tmp_path):
    from fno.forecast_v4_rules import pack_wiring

    history = pack_wiring.candle_history()
    assert history == candle_sessions(CandleRvTable(INTRADAY_FOLDER).rows())  # the one reader, first_seen_at kept
    assert pack_wiring.candle_rv() == {s.day: s.rv_session for s in history}
    monkeypatch.setattr(pack_wiring, "INTRADAY_FOLDER", tmp_path / "missing")
    assert pack_wiring.candle_history() == [] and pack_wiring.candle_rv() == {}  # no folder: empty, no error

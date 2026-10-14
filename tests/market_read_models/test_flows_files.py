"""Story P8 (data side): NSE's FII/DII cash values and NSDL's daily FPI report are archived one copy per day fetched
(both serve only their latest day), read back with the session each copy covers, checked on the way into the archive,
and downloaded daily by a plain GitHub Actions job."""

from datetime import date
from pathlib import Path

import pytest
import yaml

from fno.fo_bhavcopy import BadFile
from fno.market_read_models.flows_files import FlowSide, read_fii_dii, read_nsdl_equity
from fno.storage.content_checks import VALIDATORS
from fno.storage.snapshot_source import FiiDiiCashBySessionSource, FiiDiiCashSource, NsdlFpiDailyBySessionSource
from fno.storage.wiring import RAW_SOURCES, RUN_DATED_FLOWS, SNAPSHOT_DATASETS

FIXTURES = Path(__file__).parents[1] / "fixtures" / "flows"
NSE_FILE = (FIXTURES / "fii-dii-cash_13102026.json").read_bytes()  # NSE, fetched 14 Oct 2026 02:17 IST
NSDL_FILE = (FIXTURES / "fpi-daily-latest_13102026.html").read_bytes()
WORKFLOW = Path(__file__).parents[2] / ".github" / "workflows" / "flows-download.yml"


def test_nses_file_gives_the_session_and_both_sides_in_crore():
    flows = read_fii_dii(NSE_FILE, "fii-dii-cash.json")
    assert flows.day == date(2026, 10, 13)
    assert flows.fii == FlowSide(13465.39, 14770.52, -1305.13) and flows.dii == FlowSide(16232.97, 13793.73, 2439.24)


def test_nsdls_report_gives_the_fpi_equity_net_over_all_routes():
    assert read_nsdl_equity(NSDL_FILE, "fpi-daily-latest.html") == (date(2026, 10, 13), 2000.73)  # the equity sub-total
    bracketed = NSDL_FILE.replace(b"2000.73", b"(2000.73)")
    assert read_nsdl_equity(bracketed, "x")[1] == -2000.73  # NSDL writes a negative amount in brackets


@pytest.mark.parametrize(
    "reader, data",
    [
        (
            read_fii_dii,
            b'[{"category": "DII", "date": "13-Oct-2026", "buyValue": "1", "sellValue": "1", "netValue": "0"}]',
        ),
        (read_fii_dii, b"<html>blocked</html>"),
        (read_nsdl_equity, b"<html>maintenance</html>"),
    ],
)
def test_a_file_that_is_not_the_report_is_refused(reader, data):
    with pytest.raises(BadFile):
        reader(data, "x")


def test_new_copies_go_to_the_by_session_series_and_are_checked_on_the_way_in():
    """Judge 66: the first copies were filed by run day (kept, never taken again); every new copy is filed under the
    session it covers, in its own series."""
    assert FiiDiiCashSource.path_for(date(2026, 10, 14)) == "nse/flows/fii-dii-cash/2026/10/14/fii-dii-cash.json"
    by_session = FiiDiiCashBySessionSource.path_for(date(2026, 10, 14))
    assert by_session == "nse/flows/fii-dii-cash-by-session/2026/10/14/fii-dii-cash.json"
    assert FiiDiiCashBySessionSource.url_for(by_session) == FiiDiiCashSource.API
    assert NsdlFpiDailyBySessionSource.url_for(NsdlFpiDailyBySessionSource.path_for(date(2026, 10, 14))).endswith(
        "/Reports/Latest.aspx"
    )
    assert SNAPSHOT_DATASETS["fii-dii-cash-by-session"] is FiiDiiCashBySessionSource
    assert SNAPSHOT_DATASETS["fpi-daily-by-session"] is NsdlFpiDailyBySessionSource
    assert "fii-dii-cash" not in SNAPSHOT_DATASETS and set(RUN_DATED_FLOWS) <= set(RAW_SOURCES)  # kept, not taken
    VALIDATORS[FiiDiiCashBySessionSource]("fii-dii-cash.json", NSE_FILE)
    with pytest.raises(BadFile):
        VALIDATORS[NsdlFpiDailyBySessionSource]("fpi-daily-latest.html", b"<html></html>")


def test_the_daily_download_runs_in_the_evening_and_alerts_on_failure():
    flow = yaml.safe_load(WORKFLOW.read_text())
    assert flow[True]["schedule"] == [{"cron": "40 15 * * *"}]  # 21:10 IST
    steps = " ".join(str(s.get("run", "")) for s in flow["jobs"]["download"]["steps"])
    assert "data-snapshot fii-dii-cash-by-session" in steps and "data-snapshot fpi-daily-by-session" in steps
    assert any("failure()" in str(s.get("if", "")) for s in flow["jobs"]["download"]["steps"])

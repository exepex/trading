from datetime import date, datetime

from fno.constants import CONSOLIDATED, FILING_RESULTS, FILING_SHAREHOLDING, STANDALONE
from fno.filings.index import NseIntegratedResultsIndex, NseLegacyResultsIndex, NseShareholdingIndex
from fno.models import IST

LEGACY = [
    {"toDate": "31-Dec-2024", "broadCastDate": "09-Jan-2025 21:39:43", "exchdisstime": "09-Jan-2025 21:40:06",
     "xbrl": "https://nsearchives.nseindia.com/corporate/xbrl/INDAS_1.xml", "consolidated": "Consolidated"},
    {"toDate": "30-Sep-2024", "broadCastDate": "10-Oct-2024 18:58:00", "exchdisstime": None,
     "xbrl": "https://nsearchives.nseindia.com/corporate/xbrl/-", "consolidated": "Non-Consolidated"},
    {"toDate": "30-Jun-2005", "broadCastDate": None, "exchdisstime": None, "filingDate": "-",
     "xbrl": "https://nsearchives.nseindia.com/corporate/xbrl/OLD.xml", "consolidated": "Consolidated"},
    {"toDate": "31-Mar-2023", "broadCastDate": None, "exchdisstime": None, "filingDate": "21-Apr-2023 14:50",
     "xbrl": "https://nsearchives.nseindia.com/corporate/xbrl/LATE.xml", "consolidated": "Consolidated"},
]  # fmt: skip


def integrated_row(n: int, kind: str = "Integrated Filing- Financials") -> dict:
    return {"seq_Id": n, "type": kind, "qe_Date": "30-SEP-2026", "broadcast_Date": "08-Oct-2026 22:07:33",
            "creation_Date": "08-Oct-2026 22:08:10", "consolidated": "Standalone",
            "xbrl": f"https://nsearchives.nseindia.com/corporate/xbrl/IF_{n}.xml"}  # fmt: skip


def test_legacy_list_keeps_the_window_and_the_later_public_time():
    calls = []
    index = NseLegacyResultsIndex(lambda path, params: calls.append((path, params)) or LEGACY)
    found = index.filings("TCS", date(2023, 10, 1))
    assert [f.period_end for f in found] == [date(2024, 12, 31), date(2024, 9, 30)]
    first = found[0]
    assert first.kind == FILING_RESULTS and first.consolidation == CONSOLIDATED
    assert first.filed_at == datetime(2025, 1, 9, 21, 40, 6, tzinfo=IST)  # dissemination, 23 s after broadcast
    assert (
        found[1].url == "" and found[1].consolidation == STANDALONE
    )  # NSE's link ends in '-' when there is no XBRL file
    assert calls[0][1]["symbol"] == "TCS"  # 2005 has no time at all (NSE): never parsed; 2023 is before the window


def test_a_row_with_only_nse_filing_minute_uses_it():
    row = dict(LEGACY[3], filingDate="02-Oct-2023 14:50")
    (found,) = NseLegacyResultsIndex(lambda path, params: [row]).filings("TCS", date(2023, 10, 1))
    assert found.filed_at == datetime(2023, 10, 2, 14, 50, tzinfo=IST)


def test_integrated_list_reads_every_page_and_only_financials():
    pages = {1: [integrated_row(1), integrated_row(2, "Integrated Filing- Governance")], 2: [integrated_row(3)]}
    index = NseIntegratedResultsIndex(lambda path, params: {"data": pages[params["page"]], "totalCount": 3})
    found = index.filings("TCS", date(2023, 10, 1))
    assert [f.filename for f in found] == ["IF_1.xml", "IF_3.xml"]
    assert found[0].filed_at == datetime(2026, 10, 8, 22, 8, 10, tzinfo=IST)


def test_shareholding_list_reads_upper_case_months():
    rows = [{"date": "30-JUN-2026", "broadcastDate": "21-JUL-2026 15:44:00", "systemDate": "21-JUL-2026 15:44:06",
             "xbrl": "https://nsearchives.nseindia.com/corporate/xbrl/SHP_1.xml"}]  # fmt: skip
    (found,) = NseShareholdingIndex(lambda path, params: rows).filings("TCS", date(2023, 10, 1))
    assert found.kind == FILING_SHAREHOLDING and found.period_end == date(2026, 6, 30)
    assert found.path == "nse/equities/filings/shareholding-xbrl/TCS/SHP_1.xml"

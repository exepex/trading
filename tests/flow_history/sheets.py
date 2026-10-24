"""Rows in the layouts of NSE's FII statistics sheets (2019: four groups, numbers as floats; 2026: per-index rows,
numbers as text) and a participant-volume file, every number invented."""

from __future__ import annotations

from datetime import date

from fno.research_data.participant_oi import COLUMNS

HEADER = [["", "BUY", "", "SELL", "", "OPEN INTEREST AT THE END OF THE DAY", ""],
          ["", "No. of contracts", "Amt in Crores", "No. of contracts", "Amt in Crores", "No. of contracts",
           "Amt in Crores"]]  # fmt: skip
NOTES = [["", "", "", "", "", "", ""], ["Notes:", "", "", "", "", "", ""], ["Both buy and sell positions ...", "", ""]]


def sheet_2019(day: str = "02-Jan-2019") -> list[list]:
    groups = [[name, 10.0, 1.5, 20.0, 2.5, 30.0, 3.5] for name in ("INDEX FUTURES", "INDEX OPTIONS", "STOCK FUTURES",
                                                                    "STOCK OPTIONS")]  # fmt: skip
    return [[f"FII DERIVATIVES STATISTICS FOR {day}", "", "", "", "", "", ""], *HEADER, *groups, *NOTES]


def sheet_2026(nifty_buy: str = "7", day: str = "21-Oct-2026") -> list[list]:
    """Index futures 10 = NIFTY 7 + BANKNIFTY 3 (buy); options from two indices too."""
    return [
        [f"FII DERIVATIVES STATISTICS FOR {day}", "", "", "", "", "", ""], *HEADER,
        ["INDEX FUTURES", "10", "1.50", "20", "2.50", "30", "3.50"],
        ["BANKNIFTY FUTURES", "3", "0.40", "5", "0.60", "10", "1.00"],
        ["NIFTY FUTURES", nifty_buy, "1.10", "15", "1.90", "20", "2.50"],
        ["", "", "", "", "", "", ""],
        ["INDEX OPTIONS", "100", "5.00", "90", "4.00", "50", "2.00"],
        ["NIFTY OPTIONS", "100", "5.00", "90", "4.00", "50", "2.00"],
        ["STOCK FUTURES", "1", "0.10", "2", "0.20", "3", "0.30"],
        ["STOCK OPTIONS", "4", "0.40", "5", "0.50", "6", "0.60"], *NOTES,
    ]  # fmt: skip


def participant_volume(day: date) -> bytes:
    """Every participant bought and sold 1 contract in each group (6 in all); the TOTAL row adds them up."""
    title = f'"Participant wise Trading Volume (no. of contracts) in Equity Derivatives as on {day:%b %d, %Y}"'
    groups = len(COLUMNS) - 3
    rows = [f"{name},{','.join(['1'] * groups)},6,6" for name in ("Client", "DII", "FII", "Pro")]
    total = f"TOTAL,{','.join(['4'] * groups)},24,24"
    return "\n".join([title, ",".join(COLUMNS), *rows, total, ""]).encode()

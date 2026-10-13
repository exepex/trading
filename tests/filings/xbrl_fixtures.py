"""Small XBRL instances shaped like NSE's results files (story A12 tests)."""

from __future__ import annotations

CONTEXT = (
    '<xbrli:context id="{id}"><xbrli:entity><xbrli:identifier scheme="s">1</xbrli:identifier></xbrli:entity>'
    "<xbrli:period>{period}</xbrli:period>{dimension}</xbrli:context>"
)
DURATION = "<xbrli:startDate>{start}</xbrli:startDate><xbrli:endDate>{end}</xbrli:endDate>"
INSTANT = "<xbrli:instant>{day}</xbrli:instant>"
DIMENSION = '<xbrli:scenario><xbrldi:explicitMember dimension="d">x</xbrldi:explicitMember></xbrli:scenario>'
ROOT = (
    '<?xml version="1.0" encoding="UTF-8"?><xbrli:xbrl xmlns:xbrli="http://www.xbrl.org/2003/instance" '
    'xmlns:xbrldi="http://xbrl.org/2006/xbrldi" xmlns:in-capmkt="http://www.sebi.gov.in/xbrl/in-capmkt">'
    "{body}</xbrli:xbrl>"
)


def context(cid: str, start: str | None, end: str, dimension: bool = False) -> str:
    period = INSTANT.format(day=end) if start is None else DURATION.format(start=start, end=end)
    return CONTEXT.format(id=cid, period=period, dimension=DIMENSION if dimension else "")


def fact(name: str, cid: str, value) -> str:
    return f'<in-capmkt:{name} contextRef="{cid}">{value}</in-capmkt:{name}>'


def results_xbrl(half_year: bool = True, legacy: bool = False, bank: bool = False) -> bytes:
    """A September 2025 results file: quarter and half-year P&L, balance sheet and half-year cash flow when
    `half_year`; `legacy` gives the half-year context the quarter's dates (NSE's files before March 2025)."""
    ytd_start = "2025-07-01" if legacy else "2025-04-01"
    body = [
        context("OneD", "2025-07-01", "2025-09-30"),
        context("FourD", ytd_start, "2025-09-30"),
        context("OneI", None, "2025-09-30"),
        context("Seg", "2025-07-01", "2025-09-30", dimension=True),
        fact("DateOfStartOfReportingPeriod", "OneD", "2025-07-01"),
        fact("DateOfEndOfReportingPeriod", "OneD", "2025-09-30"),
        fact("DateOfStartOfReportingPeriod", "FourD", "2025-04-01"),
        fact("DateOfEndOfReportingPeriod", "FourD", "2025-09-30"),
        fact("Income" if bank else "RevenueFromOperations", "OneD", 1000),
        fact("Income" if bank else "RevenueFromOperations", "FourD", 1900),
        fact("RevenueFromOperations", "Seg", 400),
        fact("ProfitBeforeTax", "OneD", 200),
        fact("ProfitLossForPeriod", "OneD", 150),
        fact("BasicEarningsLossPerShareFromContinuingAndDiscontinuedOperations", "OneD", "12.5"),
    ]
    if half_year:
        body += [
            fact("Assets", "OneI", 9000),
            fact("CashFlowsFromUsedInOperatingActivities", "FourD", 300),
            fact("CashFlowsFromUsedInInvestingActivities", "FourD", -120),
            fact("CashFlowsFromUsedInFinancingActivities", "FourD", -80),
        ]
        if bank:
            body += [
                fact("Borrowings", "OneI", 700),
                fact("Capital", "OneI", 10),
                fact("ReservesAndSurplus", "OneI", 90),
            ]
        else:
            body += [
                fact("BorrowingsCurrent", "OneI", 50),
                fact("BorrowingsNoncurrent", "OneI", 250),
                fact("CashAndCashEquivalents", "OneI", 400),
                fact("Equity", "OneI", 5000),
            ]
    return ROOT.format(body="".join(body)).encode()


def shareholding_xbrl() -> bytes:
    body = context("OneI", None, "2025-09-30") + fact("ShareholdingOfPromoterAndPromoterGroup", "OneI", "71.77")
    return ROOT.format(body=body).encode()

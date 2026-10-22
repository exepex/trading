"""Pages in the layout of NSDL's FPI archive answer (21 Oct 2026 probes: 2 Jan 2019, 30 Jun 2019, 15 Oct 2026), cut to
two reporting dates and two categories, every number invented."""

from __future__ import annotations

HEADER = ("<tr><th>Reporting Date</th><th>Debt/Equity</th><th>Investment Route</th><th>Gross Purchases(Rs Crore)</th>"
          "<th>Gross Sales(Rs Crore)</th><th>Net Investment (Rs Crore)</th><th>Net Investment US($) million</th>"
          "<th>Conversion (1 USD TO INR)*</th></tr>")  # fmt: skip


def _day(day: str, rate: str = "Rs.11.1111", net: str = "(3.00)") -> str:
    return (
        f"<tr><td rowspan='7'>{day}</td><td rowspan='3'>Equity</td><td>Stock Exchange</td>"
        f"<td align='right'>10.00</td><td align='right'>13.00</td><td align='right'>{net}</td>"
        f"<td align='right'>(0.30)</td><td rowspan='7'>{rate}</td></tr>"
        "<tr><td>Primary market &amp; others</td><td>1.00</td><td>0.00</td><td>1.00</td><td>0.10</td></tr>"
        "<tr><td>Sub-total</td><td>11.00</td><td>13.00</td><td>(2.00)</td><td>(0.20)</td></tr>"
        "<tr><td rowspan='3'>Debt</td><td>Stock Exchange</td><td>5.00</td><td>1.00</td><td>4.00</td><td>0.40</td></tr>"
        "<tr><td>Primary market &amp; others</td><td>0.00</td><td>0.00</td><td>0.00</td><td>0.00</td></tr>"
        "<tr><td>Sub-total</td><td>5.00</td><td>1.00</td><td>4.00</td><td>0.40</td></tr>"
        "<tr><td>Total</td><td>16.00</td><td>14.00</td><td>2.00</td><td>0.20</td></tr>"
    )


def page(up_to: str = "02-Jan-2019", days: tuple[str, ...] = ("01-Jan-2019", "02-Jan-2019"), extra: str = "") -> str:
    totals = ("<tr><td rowspan='7'>Total for January</td><td rowspan='3'>Equity</td><td>Stock Exchange</td>"
              "<td>1</td><td>1</td><td>1</td><td>1</td><td></td></tr>")  # fmt: skip
    derivatives = ("<tr><th>Reporting Date</th><th>Derivative Products</th><th>Buy</th></tr>"
                   "<tr><td>01-Jan-2019</td><td>Index Futures</td><td>1</td><td>1</td><td>1</td><td>1</td><td>1</td>"
                   "<td>1</td></tr>")  # fmt: skip
    body = "".join(_day(day) for day in days)
    return (f"<html><form id='frmMonthly'><div id='dvArchiveData'><table><tr><th colspan='9'>Stock exchanges ...</th>"
            f"</tr><tr><th>Daily Trends in FPI Investments up to {up_to}</th></tr>{HEADER}{body}{extra}{totals}"
            f"{derivatives}</table></div></form></html>")  # fmt: skip

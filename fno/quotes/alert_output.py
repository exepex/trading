"""How a 3 pm quote command prints its #fno-desk alerts (stories A4, A4c; O2's outage days). The command's sender is
O1's `ReportedAlerts` (wired in `cli.cmd_quotes`): it prints an alert Slack did not take as "alert NOT sent: <reason>
| <text>", so the routine can post the text itself. The command prints only a sent alert's outcome, never a bare
"alert NOT sent" line without its text."""

from __future__ import annotations

from ..alerts.sender import SENT, AlertSender


def announce(alerts: AlertSender, text: str) -> None:
    outcome = alerts.send(text)
    if outcome == SENT:
        print(outcome)

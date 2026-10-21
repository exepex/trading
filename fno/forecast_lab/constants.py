"""Story FL1's fixed values and message templates (the channel IDs live in `fno/constants_channels.py`)."""

from __future__ import annotations

from datetime import time

UNDERLYINGS = ("NIFTY", "BANKNIFTY")  # owner, 21 Oct 2026 (DESK_DECISIONS row 262)
ISSUE_CLOSE = "1545"  # phase 1's one issue (owner, "Lab universe, report times and phasing")
HORIZON_SESSIONS = {"N1": 1, "N3": 3}  # sessions after the issue day; N0 comes with the 09:15 issue (FL1-2)
LEVELS = (0.05, 0.25, 0.50, 0.75, 0.95)
REPORT_AT = time(15, 45)  # O1's `lab_close` waits for it: after the 15:30 close, G13b's 15:45 issue and `candles`
SEAL_BY = time(9, 15)  # a forecast counts for a target day only if sealed before that day's open
CALIBRATION_DAYS, EDGE_WINDOW = 60, "6-12 months"
REPORT_AREA = "forecast_lab/v1/close"  # under O9's Drive data area: the report text and its posted marker

HEADER = "F&O forecast lab {day}: 15:45 report (paper research only, never an order)"
TRUST = (
    "Trust: {days} scored trading day(s) of about {needed} needed to judge calibration; a trading edge needs {edge}. "
    "One day's forecasts, of every contract, are one outcome, not many."
)
NO_ISSUE = "{underlying} {horizon} for {target} (issued {issue_day}): no forecast was sealed; nothing to score"
LATE = "{underlying} {horizon} for {target} (issued {issue_day}): sealed late ({sealed}); not shown as a forecast"
NONE_EXPECTED = "{underlying} forecasts for {target}: none expected (issued before G13b's first live day)"
SEALS_OK = "{underlying} forecasts for {target}: every one sealed in time"
NOT_IN_TIME = " {horizon}, issued {issue_day}: no forecast sealed in time (its seal check said why)"
SCORES_NOT_READY = (
    "{underlying}: the official close of {target} is archived but G13b has not scored all its forecasts yet; its match "
    "comes in a later report"
)
NOT_SEALED_YET = "{underlying} next sessions: today's 15:45 issue is not sealed yet; not shown"
MATCH_HEADER = (
    "{underlying} match: the forecasts for {target} against its official close; the latest days are matched in a "
    "later report (NSE archives the close in the evening)"
)  # owner, 21 Oct 2026 (DESK_DECISIONS): 15:45, the match lags one session, said in the report
NOT_ARCHIVED = "{underlying}: the official close of {target} is not archived yet; its match comes in a later report"
LOOKBACK_SESSIONS = 5  # a day not checked or matched yet is taken up by a later report within a week, then dropped
ALERT = "F&O forecast lab {day}: {what}"
NOT_A_SESSION = "lab close {day}: not a regular session; nothing posted"
ALREADY_POSTED = "lab close {day}: already posted and alerted; nothing sent again"
REPORT_POSTED = "lab close {day}: report to #fno-forecast: {outcome}"
REPORT_ALREADY = "lab close {day}: report already posted to #fno-forecast"
ALERTS_SENT = "lab close {day}: {sent} of {total} alert(s) sent to #fno-desk"
ALERTS_ALREADY = "lab close {day}: alerts already sent; none sent again"
NOT_POSTED = "the 15:45 report was not posted to #fno-forecast ({outcome})"
CHECK_BEFORE_REPOST = "; check #fno-forecast before any repost"  # Slack may have posted it
MAY_HAVE_POSTED = "Slack may still have posted it"  # T1's poster wording: never retried, so never posted twice

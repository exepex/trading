# Response 241: the year-end calendar gap in the frozen forecast code (A14c audit, response 239)

Asked by the orchestrator (16 Oct 2026): verify the two findings, propose the root-cause fix and how it fits the
freeze rules, and check G4 and G8 for the same pattern. NSE's 2027 holiday circular is assumed not out before 17 Nov.

## 1. Verified (strong evidence: run on main against the real calendar)

`ForecastHistory.horizon_day` (`fno/forecast/history.py:86-92`) asks the calendar for day+1 to day+45 in one call.
The calendar covers whole years and holds 2026 only, so any day whose day+45 falls in 2027 raises `CalendarError`, and
the function returns None, even when the target session is inside 2026.

| Horizon | Wrongly None (target inside 2026) | Correctly unknown (target in 2027) |
|---|---|---|
| 20 sessions (Q1, Q2, Q3, Q5) | 11 sessions, 17 Nov to 2 Dec 2026 (17 Nov should give 16 Dec; 2 Dec should give 31 Dec) | from 3 Dec 2026 |
| 10 sessions (Q4) | 21 sessions, 17 Nov to 16 Dec 2026 | from 17 Dec 2026 |

What it does:
- **Live capture (G2/G3, protocol v2).**
  - `RiskNeutralBaseline.inputs` (`baselines.py:62`) gets no target day, so Q1 and Q2 are None.
  - `book1_probabilities` (`book1_method.py:32-38`) then averages the other two baselines. Book 1's Q1 and Q2 on
    those days are therefore a two-baseline average, not three.
  - The records are written once, so this is permanent for every day captured in the gap.
- **G4 scoring (protocol v3).**
  - `OfficialOutcomes.resolve` (`forecast_scoring/resolution.py:66`) calls the same function and returns PENDING.
  - This is a delay only, not a loss. With a 2027 row in the calendar, the same call returns 16 Dec for 17 Nov and
    31 Dec for 2 Dec; I checked this on a temporary copy of the calendar. So the scores resolve correctly as soon as
    NSE's 2027 rows are added.

## 2. The same pattern elsewhere

- **G8 / protocol v4 is not affected.**
  - `fno/forecast_v4/sessions.py:18 next_scored_sessions` walks one day at a time, so it raises only when the target
    really lies beyond the calendar.
  - Nothing in `fno/forecast_v4`, `fno/forecast_v4_rules` or `fno/forecast_scoring/v4` calls `horizon_day`.
- **M1 weather (`fno/weather/wiring.py:54`)** uses that same walk with a 5-session horizon. It returns None only for
  the last few days of 2026, and that is correct.
- **Other `except CalendarError` sites** (`cards/session.py:55`, `budget/stop_rule_tracker.py:74`,
  `vix_history/checks.py:58`, intraday, quotes) look up single days or step backwards. None of them asks for a fixed
  window that is wider than the answer it needs.

## 3. Root cause

There are two causes, and the second matters more:
1. **The wide window.** `CALENDAR_LOOKAHEAD_DAYS = 45` assumes "the calendar is published ahead" (`history.py:33`).
   At the turn of the year that assumption is false.
2. **The calendar's lead time.** Even with the code fixed, every 20-session forecast from 3 Dec onward has an unknown
   target until NSE's 2027 holidays are in the calendar.
   - Those live risk-neutral values are then None for good, a correct "no forecast", and Book 1 averages two
     baselines.
   - So the code fix saves only the 11 sessions of 17 Nov to 2 Dec; the rest of the gap depends on when NSE's list
     arrives.
   - NSE has usually published the next year's trading holidays in December. That is reasoning only: I have not
     checked the dates of past circulars.

## 4. Options and the freeze rules

Every file of `fno/forecast/` is hashed by FREEZE_v2, and `fno/forecast_scoring/resolution.py` by FREEZE_v3. The
protocol says: "Any change from here is a new version, never an edit." So no code fix can land as an edit.

| Option | What it saves | Cost |
|---|---|---|
| A. Change nothing in the frozen code. Add NSE's 2027 rows the day the circular is out (A7's routine), and have O8's health check alert when the calendar ends within 60 days. | Scoring: everything (PENDING resolves once the rows land). Live: nothing in the gap. | The live risk-neutral Q1 and Q2 are None from 17 Nov until the rows land. Book 1 is a two-baseline average then. Both are visible in the records. |
| B. A new forecast protocol version whose `horizon_day` walks session by session (v4's `next_scored_sessions`), frozen with its own record. | Live: the 11 sessions of 17 Nov to 2 Dec. | A whole new version, with a new freeze, a new ledger row and its own report section, to save one baseline's input on 11 days. It must be frozen and running before 17 Nov, a month from now. |
| C. Invent 2027 rows (weekdays, no holidays) ahead of NSE. | — | Rejected: invented data. A missed 2027 holiday would set a wrong target day and score a wrong outcome. |

**Recommendation: option A** (reasoning only), plus two small things that need no freeze change:
- **A protocol note, lane 1 for the forecast protocol's owner.** For live days whose target lay beyond the calendar at
  capture time, every report labels Book 1's Q1 and Q2 "risk-neutral baseline unavailable: calendar coverage". The
  scoring may also show them apart. This is reporting only, with no change to frozen code.
- **An O8 health-check expectation:** "the session calendar ends in under 60 days" is a red line. That gives at least
  six weeks of warning every year, from about 1 Nov for 2026.

If the owner wants those 11 days kept, option B is the only honest way, and it is their call: it is a new protocol
version. Its cost is the version itself, not the code (about 10 lines plus a test).

## 5. Who decides

- **The owner:** A or B.
- **The forecast protocol's owner (G):** the label wording and where it lives.
- **O8's owner:** the 60-day alert.
- **A7's routine:** add the 2027 rows from NSE's circular.

I build none of these unless asked, because the files are not mine (one builder per function).

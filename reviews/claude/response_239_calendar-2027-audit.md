# Response 239: what every user of A7's NSE calendar does when it runs out (audit, 16 Oct 2026)

Builder session 01Vm1WnH8i9waM8EJG8zwWqg, part (a) of the orchestrator's calendar task. Read-only audit of `main` at
8fdd5a02, by an independent agent; items 1 and 3 re-read by the builder. Nothing is changed by this file. Fixes belong
to each function's owner (one builder per function).

The calendar (`research/data/calendar/nse_sessions.csv`) covers 2017-01-01 to **2026-12-31**
(`fno/research_data/calendar.py:75`). Any date past that raises `CalendarError`, whose message says to add NSE's
circular rows. NSE's 2027 circular is not published yet (likely December). O8 will warn once from 17 Nov (orchestrator,
16 Oct). The rule: every user fails loudly, by name; none falls back silently.

## Silent or misleading (earliest first)

| # | Where | Starts | What happens | Evidence |
|---|---|---|---|---|
| 1 | `fno/forecast/history.py:86-91` (`horizon_day`): G2/G3 risk-neutral baseline and Book 1 blend | **Tue 17 Nov 2026** | Asks for day+1..day+45 in one call and returns None on `CalendarError`, although the 20th session is inside the calendar. The baseline's Q1/Q2 give None; Book 1 quietly averages the other baselines only. Frozen code (G1/G2): the fix needs a protocol change | strong, re-read by the builder |
| 2 | `fno/forecast_scoring/resolution.py:66` (same `horizon_day`) | 16 Dec 2026, 22:41 IST | Forecasts made 17 Nov-31 Dec stay `PENDING` instead of being scored | strong |
| 3 | `fno/weather/wiring.py:51-55`, `v0_live.py:34-42` (M1) | Thu 24 Dec 2026 | The 5-session window crosses 1 Jan; `except CalendarError: return None` makes the colour None and v0 is recorded `MISSING` / `NOT_SCORED`, with no reason named | strong, re-read by the builder |
| 4 | `index-closes.yml`, `panel-days.yml`, `nse-margins.yml` | Fri 1 Jan 2027 | The librarian (`librarian.py:61`) and `due_session` crash. The only line says "the Drive archive step failed" (blames Drive), and the "already alerted" step assumes a line that never went | strong |
| 5 | `fno/budget/stop_rule_tracker.py:74-77` | active now | A May 2027 review date falls back to a weekday walk (31 May 2027). The printed lines note it, but the `REVIEW_REACHED` alert drops the note | strong |
| 6 | `fno/checks/validity_settings.py:51` (C4 margin freshness) | latent, 2027 days | `except ValueError: return False` reads as "margin too old", not as the calendar; masked today because the desk run crashes first | some |

## Loud but generic

The desk run (E3), market publish, forecast capture, scoreboard, review dates and others crash, and their workflows post
"run failed; see URL" at best. Correction (O8's owner, 16 Oct, checked at `fno/health/cli.py:43`): the health check
is not silent on 1 Jan; its check step catches the error and posts "health check FAILED: CalendarError". The real gap
was a failure outside that step (checkout, install, commit); O8b adds a `failure()` line for those only (3e215fbb). Only the Python-side handlers name the calendar: the 3 pm recorder, A16, the daily card, A17 cues and
A15.

## Proposals (reasoning; each owner decides)

- The one fix that removes items 1-3: ask the calendar only for the dates needed (stop at the 20th or 5th session),
  and treat "beyond the calendar" as a named stop, never None. For the frozen `history.py`, a protocol note or version
  is needed.
- Workflows: the "already alerted" steps check that a line was really sent, and health-check.yml gets the same
  `failure()` alert as the others.
- In every case, the real fix is NSE's 2027 rows, entered from its circular before 17 Nov if it is out, and otherwise as
  soon as it is published.

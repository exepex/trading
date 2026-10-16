# Response 245: the weather at the calendar's end (24-31 Dec 2026): unknown events said, v0's reason named

Builder: session 013xqaNTCbSBytKgqpfaYFqZ (M1 and P2a builder), branch `story/m1-calendar-end`. Lane 1 (a forecast
record's fields and what a screen shows). Raised by the A14c builder (response 239 item 3, routed by the
orchestrator), under the rule "every A7 user fails loudly, by name, never silently" (orchestrator, 16 Oct 2026).

## What happens (strong evidence: the code and a test on M1's own fakes)

- From 24 Dec 2026, M1's 5-session event window runs past NSE's calendar, which holds 2026 only. `horizon(d)` is
  then None (`fno/weather/wiring.py:51-55`): v0 has no colour, and the record's `events_next_5_sessions` is null.
- **The operative colour is not affected:** it is the VIX model's (decision 71), which does not use the calendar
  (`day.py:69-75`). So the day's colour and probabilities still score.
- **Two silent spots, both fixed here:**
  1. **My weather page (P2a) read null events as "no event".** On those days the screen would have shown no scheduled
     event when it does not know: misleading, and on the side that does not protect the owner. Now it shows one
     driver, "Scheduled events over the next 5 sessions not known yet: NSE's next-year holiday list is not loaded",
     with push riskier (unknown is caution; the contract has no neutral push).
  2. **M1's record said v0 was "not scored" with no reason.** It now carries `v0_status`: `scored`, or `not scored:`
     and why. Either its inputs need more closes, or "the next 5 sessions run past NSE's session calendar, so the
     scheduled events are unknown: add NSE's next-year holiday circular rows (story A7)".
- **The real fix** is NSE's 2027 rows (the A14c builder enters them when NSE publishes; O8 warns from 17 Nov).

## Notes

- `v0_status` is a new field in future records only. The 2,409 committed back-fill records stay as written, and no
  reader requires the field.
- Changing `fno/weather/` changes M1's `method_sha256` for new records (an audit hash; nothing compares it with old
  records: grep).

## Tests

- `tests/market_read_models/test_weather_page.py`: null events give the "not known yet" driver.
- `tests/weather/test_checklist_v0.py`: a calendar ending inside the window gives the named reason; a normal day none.
- `tests/weather/test_records_and_capture.py`: the record's fields include `v0_status`.
- Full suite: 7,071 passed; ruff, format and imports clean.

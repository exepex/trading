# Response 331: FL1-1f, judge 547 answered

From the FL1 builder (session_01FWkBH4zNAEFSEpjUzVEgnd) to Judge E, 23 Oct 2026. Branch
`story/fl1-1f-evening-top-block`. Judge 547 judged 5460bfcc and failed it on two findings. I accept both. I checked
each against the code, and both are real honesty faults in the record line. Both were already fixed at b801bc28, from
the orchestrator's early note. This round adds the judge's own probes as pinned tests.

## F1: the back-test counted the last 30 back-tested sessions, not those among the last 30: accepted

- **Check:** `track_record` took `[p for p in points if not p.live][-30:]`. With 30 back-filled sessions followed by
  10 live ones, it printed "Back-test (last 30 days): 30 of 30" for sessions 11 to 40 sessions old.
- **Fix:** the window is the last 30 sessions (`points[-30:]`). The back-test counts the back-tested sessions inside
  it, and `TrackRecord.window` carries the window's length. The label says exactly what is counted:
  - "last 30 days" only when all 30 were back-tested;
  - "N of the last 30 days" otherwise;
  - "none in the last 30 days" when there are none.
- **Pinned:** `test_judge_547_f1_thirty_back_filled_then_ten_live_counts_only_the_last_30_sessions` gives
  `TrackRecord(10, 10, 20, 20, 30, 10)` and "Back-test (20 of the last 30 days): 20 of 20". Reverting the fix makes
  it fail.

## F2: the light before "Live so far" was rated on the mixed 30 days: accepted, fixed differently

- **Check:** `plain.light` read `index.right` and `index.scored` over the mixed last 30. With one live day, the 🟢
  was almost all back-test, yet it stood before the live count.
- **Fix:** I chose to rate the light on what it stands next to, not to move it. With a record (`index.track`), the
  light is rated on live checks only: the newest 30, with FL1-1c's thresholds (25 or more green, 24 amber, 23 or
  fewer red).
  - Until 30 live checks exist it is "none". The Slack prefix reads "⚪ too few live days to rate |", and the page's
    `light_word` is "Too few live days to rate".
  - The reason for this choice: the owner's ask was a live record kept apart from the back-test. A light that rates
    the back-test would put a colour on the history, not on the live forecasts the owner is judging.
- **Pinned:**
  - `test_judge_547_f2_one_live_day_never_shows_a_colour_before_the_live_count` checks one live day and 28 of 29
    back-test: the line starts "⚪ too few live days to rate | Live so far: …";
  - `test_the_light_rates_live_checks_only_the_newest_30` checks 30 live checks with 5, 6 or 7 misses (green,
    amber, red) and 29 live (none).
  - Reverting the fix makes them fail.
- **Consequence for the owner (reasoning only):** the light stays grey for about six weeks from 23 Oct, until 30
  live sessions exist. That is the honest state.

## Real data (read-only, 23 Oct evening, nothing posted or written)

- NIFTY: "⚪ too few live days to rate | Live so far: 1 day, inside “almost certainly” 1 of 1 | Back-test (29 of the
  last 30 days): 24 of 29".
- BANKNIFTY: the same, with back-test 27 of 29.
- Status line: "✅ All systems normal".

## Gates

The gates for the head that carries this response are in my message to the orchestrator.

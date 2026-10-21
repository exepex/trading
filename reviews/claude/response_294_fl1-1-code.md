# Response 294: FL1-1 code, the 15:45 forecast lab report (builder's claims, for Judge E)

Builder: session_01FWkBH4zNAEFSEpjUzVEgnd. Branch: `story/fl1-forecast-lab`. Story text: PASS at Judge E 403.4.
Scope: phase 1 only (owner's scope freeze, 21 Oct 2026), so FL1-1 without FL1-1b's contract tracking. FL1-2 is not
started.

## What is built

| Part | Files |
|---|---|
| Channel constants, and a record scan that allows exactly three channel IDs (criterion 7) | `fno/constants_channels.py`, `fno/record_scan/catalogue.py`, `tests/record_scan/test_patterns.py` |
| FL1's port onto G13b, which FL1 owns, plus the one adapter over G13b's real reader | `fno/forecast_lab/ranges.py`, `g13b_adapter.py` |
| Match section: the seal must come before the target day's 09:15 open, and G13b's `late` flag counts. Missing or late forecasts are shown and alerted, never skipped (criterion 2) | `match.py` |
| Scoreboard (G13b's own scores, never recomputed, never pooled across method SHAs) and the trust line (criteria 3-4) | `scoreboard.py` |
| `lab close`: closed day, write-once report, rerun reuses the stored text, posted marker, exit contract (criteria 1, 5) | `lab_close.py`, `records.py` (O9 Drive data area with SHA receipts), `cli.py` |
| Composition root: G13b's LIVE and SCORES synced verified first, T1's poster pointed at #fno-forecast | `wiring.py` |
| O1 step `lab_close`, last, after `candles`: `Alerted(LiveFrom(NotBefore(15:45, CommandStep)))`, off (`live_from: null`). Agreed with the O1 builder; diff sent to them | `fno/daily/wiring.py`, `fno/constants_operations.py`, `config.yaml` |
| Rules | `CLAUDE.md`: the routing line and one routine sentence |

## Tests (`tests/forecast_lab/`, plus 4 O1 and health tests updated for the new last step)

The tests cover:
- a closed day;
- a session day with matched and scored rows;
- a late seal and a missing issue (shown and alerted);
- a rerun that posts nothing;
- a report written but not posted (it posts the stored text, not a rebuilt one);
- a Slack "may have posted" outcome (marked posted, never retried, exit 1);
- method versions kept apart;
- the receipt-checked read-back of records (a damaged copy raises);
- CLI exit codes, the `main` registration and the O1 step's shape;
- not live means no wait until 15:45.

`test_g13b_integration.py` uses G13b's real objects end to end:
- builds a record with G13b's own `RangeBuilder`;
- seals it with its own `SealCheck`/`Seals` and scores it with its own `resolved`/`row_scores`;
- reads it back through `RangeForecasts`/`RangeScores` and FL1's adapter, then into the report's sections.

A change to G13b's shape fails there.

## Open: what I could not finish, and why

1. **The O11 replay (criterion 8) is still a strict xfail, with a specific reason.** The replay has no G13b
   `price_ranges` step. Running `lab close` there would only alert "no forecast was sealed" on the recorded day, which
   is correct behaviour but no real coverage. Proposal: add G13b's issue to the replay (O11 is mine) together with
   `lab close`, as a follow-up. Evidence: reasoning only.
2. **Fixed before judging (the commit after ad13de4e): the match section matches the previous session, not today.**
   At 15:45 today's official close never exists: NSE's index-close file is archived in the evening (G13b builder:
   rows land about 23:00-02:13 IST). As first built, the match section only matched targets equal to the report day,
   so on live days it would always have said "not archived" and never shown a match. That was a design error, not a
   lag. It now matches the targets of the session before the report day, whose close is archived and (with G13b's
   proposed daily score step before 15:45) scored. A report day the routine misses leaves that session's targets out
   of the match section; they still count in the scoreboard and the trust line. Evidence: strong (G13b's archive
   times; `test_the_report_matches_the_previous_session...`, `test_an_unarchived_close_defers_the_match`, and the
   G13b integration test now runs a 21 Oct report matching 19 Oct's targets across the test calendar's 20 Oct
   holiday). An owner option remains: a provisional same-day match on A16's 15:30 mark, clearly labelled (not built).
3. **No daily `pricerange score` step exists in `DAILY_RUN_STEPS`.** Without it, the scoreboard only moves when someone
   runs G13b's score command. This is G13b's function, not mine. The G13b builder agrees and has proposed an O1 step
   `price_range_scores` right after `price_ranges` (before 15:45) to the orchestrator; nothing built yet.

The step stays off (`daily.live_from.lab_close: null`) until the owner sets a date. It also needs the bot in
#fno-forecast, proved by one read-only `conversations.info` call, never a test post.

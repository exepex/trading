# Response 309: FL1-1d-1 code, the report in two editions (builder's claims, for Judge E)

From the FL1 builder (session_01FWkBH4zNAEFSEpjUzVEgnd), 22 Oct 2026.
- **Branch:** `story/fl1-1d-two-editions` at 506b2481, with `main` merged.
- **Story text:** `docs/stories/FL1-1d-two-editions.md`. Judge 438.1 passed it at dfacef5a. 2b2c5724 added only
  1d-2 items: the librarian rules and 30-day miss reasons.

## What is built (design items 1, 2, 4 in part, 7 and 8; criteria 1, 2, 5, 6 and 7)

**One run for both editions** (`fno/forecast_lab/edition_run.py`, which replaces `lab_close.py`).
- `EditionRun` carries over FL1-1's write-once post, alerts and rerun rules, plus three new rules:
  - an edition posts only from its own `forecast_lab.live_from` date. Both dates are null in `config.yaml`, so
    nothing is live until the owner signs off the design;
  - the morning is never posted at or after 09:15. One alert says so, and a rerun sends no second alert. A report
    written before 09:15 but not posted is never posted late;
  - a failed post alerts #fno-desk itself, once, with that day's alerts. The editions run from the owner's routines,
    outside O1's `Alerted`.

**What goes into each edition** (`composers.py`).
- The evening keeps FL1-1's seal checks and matches, and adds the page's verdicts.
- The morning adds the confirmation (below), and its record keeps what it confirmed in `matched`.

**The page in both editions** (`page/builder.py`).
- **The morning** shows the forecasts sealed the previous session for today ("today") and the next sessions. The
  "when" words now follow the sessions to each row's own target: for example, "in 2 trading days" for the N3 issued
  the day before.
  - The price is the previous session's official close, labelled "close Fri 23 Oct". If that close is not archived,
    the page shows the 3 pm price and says so.
  - If the previous session's issue is missing, the page says "today's forecast is missing (none sealed on ...)".
  - The newest scored session it expects is two sessions back. Measured fact from the code: G13b scores the previous
    session only in the 14:33 routine, so at 08:50 a one-session rule would print "stale" every morning.
- **The evening** checks today's forecast (the previous session's N1, aimed at today) against today's close as read,
  through the new `TodayCloses` port.
  - The result is labelled "NSE's close; the official file confirms it tomorrow".
  - The words are the designer's: ✓ Correct, ⚠ Close call, ✗ Missed.
  - If no close was read, the page says so in one system line and checks nothing.
- **Light and record:** the evening's check counts in the light and the record.

**Confirmation** (`confirm.py`). Each morning compares the earlier evenings' verdicts with NSE's official closes,
through G13b's `Outcomes`. Each verdict ends one of four ways:
- **confirmed** (the closes agree within 0.01 point);
- **a different close, same verdict:** a line, with no alert;
- **a changed verdict:** a CORRECTION line, plus one alert;
- **official close not archived yet:** taken up by a later morning, within 5 sessions, and never confirmed twice.

**Records:**
- one Drive area per edition: `forecast_lab/v1/morning` and `forecast_lab/v1/evening`;
- each evening record keeps its verdicts, with the band they were checked against.

**Commands:** `python -m fno lab open` and `python -m fno lab close`.

**O1's `lab_close` step is removed, under the O1 builder's 4 conditions:**
1. **Removed:** `DAILY_RUN_STEPS`, `LIVE_STEPS`, its wiring and import, the config key, and FL1-1's test-list
   changes. `candles` is the last step again.
2. **Old run logs:** `tests/forecast_lab/test_old_run_logs.py` shows O8's check is not upset by an old `lab_close`
   entry (`not_live` or `ok`), and that no committed run log names the step. The other readers only look steps up by
   name (scoreboard, card checks, desk); the day runner counts only failed or refused results. Reading of the code.
3. **Ordering:** the report was null until now and `forecast_lab.live_from` is null too, so no 15:45 post can take
   the evening's record.
4. **Committing:** the CLAUDE.md section "Morning and evening forecast routines" commits only that edition's
   receipts. A refused push is retried once after a pull. If it fails again, "receipt NOT pushed" goes to #fno-desk.

**The end-to-end replay (O11)** now runs the evening edition at 20:05 after the day run, instead of as a step.

## Not built here, said plainly

- **`TodayCloses` has only `NoTodayCloses` so far.** A4h's reader belongs to the A4 builder, so until it lands the
  evening says "today's close was not read (A4h's close reader is not built yet)" and checks nothing.
  **The evening edition cannot check anything until A4h exists.**
- **Confirmation needs the official close archived.** O6's job archives it at 21:11 and later, while the file
  appears at 23:20, so a GitHub retry usually lands after 08:50. Most mornings will therefore say "not archived yet",
  until 1d-2's morning `index-close` fetch, which waits for the A9 owner. Reasoning from the measured times
  (response 304).
- **The interim drawing is still used:** the edition's title and time, the result line and the confirmation lines.
  The designer's renderer replaces it after the owner's sign-off.
- **The stored prompts changed** from response 304's drafts. They now name the one CLAUDE.md section:
  - "Run the morning routine in CLAUDE.md, section 'Morning and evening forecast routines'."
  - "Run the evening routine in CLAUDE.md, section 'Morning and evening forecast routines'."
  The schedules are unchanged: 08:38 and 19:53 IST. The A22 pre-open routine, merged meanwhile, starts at 08:36 in
  its own session.

## Checks (builder's claims)

- **Gates:** one full run on the branch merged with `main` (after A22's merge): 9,145 passed, 16 xfailed.
  - `ruff check` clean; `ruff format --check` 1,711 files; imports clean; record scan clean (7,421 files).
- **Tests:** 97 FL1 tests. New this round: `test_page_editions` (10), `test_confirm` (6), `test_morning_run` (5),
  `test_old_run_logs` (3), `test_wiring_editions` (2), plus additions to the records, maker and plain tests.
- **15 planted mutations, 15 caught:** 10 at first. The 5 survivors got new tests, then all 15 were re-run:
  - the 09:15 boundary;
  - the live date ignored;
  - a failed post not alerted;
  - the late check placed before "posted";
  - a 50%-only verdict change;
  - the close tolerance;
  - confirming twice;
  - the morning reading today's issue;
  - past targets shown;
  - a wrong target checked;
  - the morning stale rule;
  - the provisional label;
  - the "today" word;
  - the verdict's day;
  - verdicts not read back.
- **Visual:** the synthetic morning edition was drawn with Chromium at 600 px; no market data was used.

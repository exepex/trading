# Judge 683: O14, one retry policy for failed commands, story text (story/o14-retry-policy @ 912cb521f)

**FAIL on 4 should-fix, text round 1 of 2, judge F (judge E the other; not read). Lane 1.** Own session
(session_01A8XfbTUVgeeEpqatHaWbtP). Labels: strong, some, reasoning only.

## Facts checked (on main)

| Claim | Result | My evidence |
|---|---|---|
| The owner's row and words | TRUE | `DESK_DECISIONS.md:350`, quoted exactly |
| Section 2: 600 s per command; A4's 60 s gap; pack until 15:10; 429 pause 60 s; NSE 1 s spacing and 15-minute cool-off; GW1a +5/+10 minutes, 3 tries | TRUE | `steps.py:24`, `recorder.py:65`, `config.yaml:164`, `groww_rate_guard.py:15`, `http_pacing.py:16-23`, GW1a lines 30-31 |
| `fills_by` 15:20; `RETRIED_ON_RERUN` = exits and marks; `test_late_retries.py` | TRUE | `config.yaml:167`, `daily_run.py:84`, `tests/timetable/` |
| GW1a: 38 x 3 = 114 sign-ins, under 150 | TRUE | GW1a lines 35-37 |
| A22 "no retry of the whole command"; candle window "09:10:00-09:10:59" | **FALSE** | see finding 1 |
| Design: one interface (`RetryPolicy`) with one strategy, wired in composition roots; one alert, no text; `fills` and the school kept final (recommended) | SOUND | read |

Gates (trial merge with main; only `.md` changes): record scan clean (9,545 files); doc-reading tests 963 passed, 13
xfailed.

## Findings

1. **Should fix: A22 already retries inside its windows (strong evidence).**
   - `fno/preopen/run.py:1-6`: each part is read at its window's opening, then every 30 s, the last at its
     `last_read_margin`. CLAUDE.md's candle read is 09:10:00-09:10:45, with the window to 09:11:00; the story says
     09:10:59.
   - Section 4 still puts a second loop (5 s base) around each A22 read. That is the double retry the same table
     rejects for A4 ("an outer retry would start a second capture").
   - Fix: A22 is "not wrapped", like A4 (or the story replaces its loop explicitly), and the times are corrected.
2. **Should fix: retries add Groww calls, and A16's marks overlap the 3 pm capture (strong evidence).**
   - "A retry adds no call beyond what the step's first attempt would have made" holds for one attempt only. Each retry
     repeats the whole attempt: an A16 mark reads its chains and every picked contract
     (`intraday/groww_source.py:68-80`, which already asks once more for failed quotes). Five retries inside the 120 s
     window is up to 6 times the calls.
   - A16 marks every 15 minutes, including 14:30, 15:00 and 15:15. `config.yaml:15` already moved `v4` to 14:32
     "after A16's 14:30 mark (Groww cap; 25 Oct)". A retried 14:30 or 15:00 mark competes with the `v4` and 3 pm parts
     for Groww's per-minute budget, which risks the day's 3 pm record.
   - Fix: no Groww retry of a mark that overlaps a 3 pm or `v4` window (or one counted in a shared Groww call budget);
     state the calls per retry; add a criterion with a plant (a 15:00 mark retried during A4's window).
3. **Should fix: which record-writing steps may be retried is left to the code (reasoning only).**
   - Section 6 builds "the table of every step, safe or not" with the code. The steps write lane-1 records:
     `forecasts_v4`, `v4_release`, `book1`, the score steps, `recommend`, `premium_ranges`.
   - The default makes a timeout retryable. A child stopped at its 600 s limit may have uploaded to Drive before its
     commit, and a retry writes again.
   - The text judges cannot check that decision, and criterion 5 tests only one safe command step plus `exits`.
   - Fix: put the initial table in the text: each step, its write-once guard (file and rule), and safe or not, with
     not safe as the default. Add the plant "a not-safe step marked safe" to criterion 5.
4. **Should fix: the Groww child budget leaves no margin, and a child's sign-in failure is not detectable as written
   (some evidence).**
   - 114 + 12 x 3 = 150, exactly Groww's 24-hour limit (GW1a line 14: going over blocks the next morning).
   - The circuit is "per process". A retried child signs in afresh, so O14 must learn from the child that its failure
     was a sign-in failure. Section 5 does not say how (the class in the child's last line? its exit?). If it cannot
     tell, every retry of a failing Groww child spends 3 sign-ins, the very case the worst case counts.
   - Fix: say how the parent reads the child's failure class, never retry after a sign-in class, and leave a margin
     under 150, or recompute from GW1a's count.

## Minors

1. "The end of the run otherwise" is not a time. Name each step's deadline (for example `candles` and the close reads).
2. One owning document: section 2 restates other stories' loops; one line and a link each would do. Section 4's
   "O14 only counts its attempts in the escalation line" for the 3 pm parts is unclear, since they alert themselves.
   Say whether O14 sends anything for them.

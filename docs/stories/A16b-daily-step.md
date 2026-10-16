# Story A16b-d: the candle back-fill as the daily run's last step

**Repository:** trading · **Lane:** 1 (Groww, Drive, the daily routine) · **Size:** S · **Builder:** A16b/A17 builder
(session 01MBnbVU) · **Plug-in check:** O1's owner (session 014zYLf1)

**Description:** As the volatility analyst, I want each finished session's 15-minute NIFTY candles archived and their
candle-close RV row written the next day, without anyone running the back-fill by hand. Two facts drive this:
- the owner's rule of 16 Oct 2026 ("external data must be up to date"; audit Part A2: "A16b ... no daily schedule");
- Groww may stop serving old contracts [some evidence: on 15 Oct it still served the expired Aug and Sep 2026
  contracts; how long it keeps them is unknown].

**Why a daily-run step and not a workflow:** the command needs Groww's key. The owner decided on 13 Oct 2026 never to
put a broker key in GitHub (DESK_DECISIONS rows 60 and 206). On 16 Oct the orchestrator chose option (a): a step of
O1's daily run, which already runs in the owner's 14:33 routine with the key. The routine's stored prompt only points
at CLAUDE.md, so no scheduled task changes.

**Scope.** In:
1. **Name:** `candles` is the last entry of `DAILY_RUN_STEPS` (`fno/constants_operations.py`), after `card`. O8 reads
   that tuple, so a day without the step counts as a miss.
2. **Step:** one entry in the steps dict of `fno/daily/wiring.py`:
   `Alerted("candles", NotBefore(CommandStep(processes, lambda day: CATCH_UP_COMMAND, candle_folders(), git.changed),
   CATCH_UP_FROM, waiter), alerts)`.
   - `CATCH_UP_FROM` is A16's last mark (`slots.py`) plus 3 minutes, a named constant in `backfill_daily.py`.
   - It has no `live_from` date (always on from the merge, as `quotes` and `book1` are).
   - It has a start time, not a cutoff: it starts no earlier than 15:33 IST (see "Groww load").
   - After an E3 stop (`RunStopped`) no later step runs, so that day has no catch-up; the next day's run picks the
     missed session up, because only windows with sessions still to write are fetched.
3. **Pathspecs:** they come from a new `fno/intraday/backfill_daily.py`, `candle_folders()` (M1's `record_folders()`
   pattern). It lists exactly the back-fill's own files:
   - `research/data/intraday/rv-candle/`: the rows and `deferred.csv`;
   - `research/data/manifests/groww-candles/`: the Drive copies' manifest rows;
   - `research/data/manifests/index-close.csv`: an A9 row, written only when the back-fill had to fetch NSE's
     index-close file itself because it was not yet in Drive. Normally index-closes.yml has archived it, and nothing
     changes here.
   - Today these paths are defined inside `backfill_wiring.py`, which imports Groww. They move to the new module, so
     `fno/daily/wiring.py` never imports Groww code.
4. **Command, unchanged:** `python -m fno intraday backfill`, with no arguments.
   - Its default end is the latest finished session: yesterday before 21:00 IST, so at 15:33 it is yesterday.
   - Windows with no session still to write are not fetched.
   - It reads Groww only through A16's `ReadOnlyGroww` allow-list.
   - It exits 1 when any session is deferred or the run stopped. O1 then records `failed` with the last printed line
     and posts one #fno-desk line; the day goes on.
   - A deferral is a real failure, not an expected wait. At 15:33 on day d+1, Groww's candles for day d are out, and
     NSE's index-close file for d has been out since d's evening. So a deferral means a Groww, Drive or NSE call failed,
     or NSE's file is still missing a day late. Either way the session is not captured, and under the owner's
     16 Oct rule that must alert. It is not printed as "nothing written" (refused).
5. **CLAUDE.md:** one clause in "Daily desk routine" step 2, after "T1's card in #fno-desk": "and, from 15:33 IST
   (after A16's 15:30 mark), A16b's candle catch-up (`intraday backfill`: yesterday's 15-minute candles, read-only
   Groww)". Sent to O1's owner for its check.
6. **One schedule:** nothing else runs `intraday backfill`. The rows through 14 Oct were written by hand from this
   builder's session (data commit 1d68c447, 15 Oct). No workflow, routine or scheduled task calls it: checked in
   `.github/workflows/`, CLAUDE.md and the account's scheduled tasks on 16 Oct. So nothing has to be retired.

Out:
- any change to the back-fill's logic, files or Drive layout;
- A16's marks;
- the O9 move of data files to Drive (O9 decides that for every table later).

**Timing (strong evidence, measured):**
- The back-fill took about 1.9 s per new session. The 2021-2026 run was 45 min 16 s for about 1,430 sessions; the
  dry run of Q1 2020 was 1 min 56 s for about 60 sessions (response 122).
- Each new session costs one Groww 1-minute call (paced at 0.5 s or more) and two Drive uploads. Each run makes one
  15-minute call for the newest 90-day window.
- So a normal day (one new session) takes about 3-6 s, including start-up.
- A long-gap day is about 2 s per missed session: 10 sessions (two weeks) take about 20 s.
- O1's 600 s limit stops a gap of more than about 300 sessions (over a year). That run commits nothing, but its Drive
  copies stay, so the next day's run skips the windows already archived. This limit is stated, not guarded.
- **Groww load: the step waits for A16's last mark.** The evidence is strong:
  - A16 measured that one Groww key gives about 5 quotes a second safely (A16 story, "Rate limit").
  - On 16 Oct, every mark taken by two runs at once lost 74-87 of about 224 quotes to Groww code 429
    (`fno/intraday/claims.py`).
  - A16's marks take about 53 s at that pace, and the last is 15:30 (15:30-15:31).
  - The card can end before 15:16, which is inside the 15:15 mark. So a catch-up started right after the card could
    add 2 calls a second to a running mark and cost it quotes.
  - The step therefore starts no earlier than 15:33 IST: after the 15:30 mark, with 2 minutes' margin. Its calls then
    meet no other Groww user of the routine.
  - How it waits: a generic `NotBefore(step, at, waiter)` DayStep in `fno/daily/steps.py` (O1's owner, 16 Oct). It
    waits through the run's `ServicingWaiter`, so a quote part still running is serviced. A day already past `at`
    starts the step at once.
  - **Side effect:** the routine session ends about 15:34 instead of about 15:20, so it runs about 14 minutes longer
    every session day.

**Writes:**
- Drive (owner's raw area): one 15-minute window copy and one 1-minute copy per new session.
- Repository: the files listed under Pathspecs. These hold counts, SHA-256 values, RV and gaps, never a price (A16b
  criterion 9, `test_no_repository_file_holds_a_price`).

**Failure record:**
- the run journal `journal/runs/<date>.json` (status, reason, exit code), committed by O1;
- one #fno-desk line from `Alerted`;
- O8's freshness row for A16b, if O10 adds it: a row for the previous session in `rv-candle/` by the end of the
  routine.
- No row in O10's `capture_errors.csv`: the journal is the one record of each daily-run step, and O8 reads it (O1's
  owner, 16 Oct; O10 covers only jobs outside `daily run`).

**Acceptance criteria:**
1. `DAILY_RUN_STEPS` ends with `candles`, and the built steps dict has exactly one `candles` step: an `Alerted`
   wrapping `NotBefore(15:33)` around a `CommandStep` whose arguments are `("intraday", "backfill")`. A planted clock
   at 15:20 sleeps until 15:33 before the command starts; at 15:40 it does not sleep. Test: the graph walk in
   `tests/daily/test_steps.py`'s style.
2. Its pathspecs equal `candle_folders()`, and `backfill_wiring.py` builds the same three paths from that module.
   Test: one source for the paths.
3. A fake child process that exits 1 with the line "deferred 1" is recorded `failed` with that reason and gives one
   alert, and the step after it still runs. A fake that exits 0 commits only the three pathspecs. These are O1's own
   behaviours, shown once for this step.
4. `fno/daily/wiring.py` imports no Groww module (import-closure test like A16b's `test_read_only.py`), and the
   back-fill's existing read-only tests still pass.
5. The first real routine run after the merge is cited in the claims file: its journal entry and the new
   `rv-candle/` row for the previous session.
6. The gates pass; no file or class is over 350 lines.

**Depends:** O1 (merged), A16b (merged). **Status:** text for O1's owner and the orchestrator.

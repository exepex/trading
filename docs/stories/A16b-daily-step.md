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
   `Alerted("candles", CommandStep(processes, lambda day: ("intraday", "backfill"), candle_folders(), git.changed), alerts)`.
   - It has no `live_from` date: the back-fill has run live since 14 Oct, so the step is on from the merge.
   - It has no cutoff.
3. **Pathspecs:** they come from a new `fno/intraday/backfill_folders.py`, `candle_folders()` (M1's `record_folders()`
   pattern). It lists exactly the back-fill's own files:
   - `research/data/intraday/rv-candle/`: the rows and `deferred.csv`;
   - `research/data/manifests/groww-candles/`: the Drive copies' manifest rows;
   - `research/data/manifests/index-close.csv`: an A9 row, written only when the back-fill had to fetch NSE's
     index-close file itself because it was not yet in Drive. Normally index-closes.yml has archived it, and nothing
     changes here.
   - Today these paths are defined inside `backfill_wiring.py`, which imports Groww. They move to the new module, so
     `fno/daily/wiring.py` never imports Groww code.
4. **Command, unchanged:** `python -m fno intraday backfill`, with no arguments.
   - Its default end is the latest finished session: yesterday before 21:00 IST, so at about 15:20 it is yesterday.
   - Windows with no session still to write are not fetched.
   - It reads Groww only through A16's `ReadOnlyGroww` allow-list.
   - It exits 1 when any session is deferred or the run stopped. O1 then records `failed` with the last printed line
     and posts one #fno-desk line; the day goes on.
5. **CLAUDE.md:** one clause in "Daily desk routine" step 2 names the candle catch-up after the card.

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
- **Groww load:** at most about 2 calls a second, starting after the card (about 15:20 or later), when the 14:55-15:13
  captures and the 15:15 snapshot are done. A16's 15:30 mark may overlap with it. Both are paced read calls, a few in
  total, far below the per-key limit [reasoning only: Groww does not publish its per-key limit for these calls].

**Writes:**
- Drive (owner's raw area): one 15-minute window copy and one 1-minute copy per new session.
- Repository: the files listed under Pathspecs. These hold counts, SHA-256 values, RV and gaps, never a price (A16b
  criterion 9, `test_no_repository_file_holds_a_price`).

**Failure record:**
- the run journal `journal/runs/<date>.json` (status, reason, exit code), committed by O1;
- one #fno-desk line from `Alerted`;
- O8's freshness row for A16b, if O10 adds it: a row for the previous session in `rv-candle/` by the end of the
  routine.
- Open point for O10 and O1, not built here: whether O10's `capture_errors.csv` should get one row per failed
  daily-run step, written by O1's `Alerted`. That would make the routine's failures land in the same file as the
  workflows' failures, instead of each step writing its own row.

**Acceptance criteria:**
1. `DAILY_RUN_STEPS` ends with `candles`, and the built steps dict has exactly one `candles` step, an `Alerted`
   wrapping a `CommandStep` whose arguments are `("intraday", "backfill")`. Test: the graph walk in
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

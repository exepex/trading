# Response 312: A4h code, today's index close read after 15:30 (builder's claims, for Judge F)

Builder session 01MKtUHByHsR9cNwaP5KhFYH, branch `story/a4h-close-read` at 9fb8618c. The story text passed in judge 440
addendum 2 (2524cbe5) and is merged (a391ff09). This is lane 1: it is not merged, and I merge only after your PASS.

## What it is

- **The command.** `python -m fno closes read [--recheck]` lives in `fno/close_read/` (11 files, the largest
  103 lines):
  - `answer` holds the stamp rule;
  - `source` is `CloseListSource` with its NSE adapter;
  - `store` is `ClosesStore` with its Drive adapter: O9's `DataStore`, and receipts for which files exist;
  - `official` is `OfficialCloses` over `build_index_close_files`;
  - `confirm`, `reader`, `records`, `constants`, `cli`, and `wiring` (the composition root).
- **O1.** `close_read` (NotBefore 15:40) and `close_recheck` (NotBefore 16:00) are the last two entries of
  `DAILY_RUN_STEPS`, after `lab_close`. Each is `Alerted(LiveFrom(NotBefore(CommandStep)))` on
  `receipts/data/closes/` only. `daily.live_from.close_read` and `close_recheck` are both `null`.

## Criteria

| # | Criterion | Evidence |
|---|---|---|
| 1 | The stamp decides | `test_answer.py`: stamps 15:30, 15:31 and 19:55 count; refused are today 15:29, the previous session, an empty stamp, an unreadable stamp, a missing index, an unreadable value and an error page with no rows. `test_reader.py`: 3 tries 60 s apart, and the fake counts calls, so a 4th try is never sent; an error's message is withheld. A special or muhurat day prints `nothing written: ...`, exits 0, and `fno/daily/steps.py`'s `outcome()` records it `refused` (read and recheck) |
| 2 | Write-once and receipts | `test_store_wiring.py`: Drive `data/closes/...` plus its receipt; the same bytes again are a no-op; different bytes raise `RawFileConflict`; `written()` reads the receipts. `test_reader.py`: a rerun writes nothing |
| 3 | Calendar and gate | A closed day reads nothing. A hand run before 15:40 (16:00 for the recheck) prints `too early: before 15:40` and exits 1. One constant serves the hand run and O1 |
| 4 | Confirm | `test_confirm.py`, against 21 Oct's real official values: 22811.35, .34 and .36 confirm; .33 records `differs by 0.02` and alerts once; VIX's 0.02 is recorded without an alert; a day with no official file waits, then alerts once at the second session after it (a write-once `.overdue.json`) and never again; a confirmation is never rewritten; today is never confirmed; a damaged file prints its line |
| 5 | O1 | `test_daily_steps.py`, on the real tuple: `DAILY_RUN_STEPS[-2:]`, `lab_close` before `close_read`, both after `candles`; wrappers, gates, arguments, pathspecs; not live means no wait and no read. Extended, never loosened: `test_day_run` (both call lists and the rerun test's new calls), `test_steps`' live dates, health's step string, and the candle and lab order tests (now `[-4:]`) |
| 6 | No Groww, no orders | `test_daily_steps.py` parses every import in `fno/close_read/`: no Groww, order or desk module. `check_imports` is clean |
| 8 | No level in a printed line | `test_no_levels.py`: the read, rerun, recheck (every index moved), a refusal, a read at recheck and a confirm with differences and alerts all run. The planted levels, moved levels and official values appear in none of the lines or alert texts in any of 7 forms (`22811.37`, `22,811.37`, `22811.4`, `22,811.4`, `22811`, `22,811`, the raw float) |
| 9 | Second read | `same` / `differs by 0.05` per index; a rerun writes nothing; with no first read, the recheck becomes the record (`read: recheck`), then both kinds of rerun are "already" |
| 10 | Gates | 9208 passed, 16 xfailed; ruff and format clean; `check_imports` clean; golden check "unchanged"; no file over 350 lines |
| 7 | First 5 live sessions | Owed after merge and go-live (both `live_from` dates), plus the e2e fixture's child once the date is on or before 14 Oct |

**Planted bugs, 10 of 10 caught** (each made, the tests run, then reverted):

| Planted bug | Tests failing |
|---|---|
| 15:30 refused (`<=`) | 8 |
| 4 tries | 1 |
| tolerance 0.02 | 4 |
| overdue alerted twice | 1 |
| today confirmed | 1 |
| a special day treated as closed (no `nothing written:`) | 4 |
| one gate for both steps | 1 |
| the recheck run twice | 1 |
| VIX alerting | 4 |
| a renamed step | 1 |

The level-in-line plant (a level added to the read line) also fails criterion 8's test.

**Live smoke test** (read-only, nothing written; 22 Oct about 05:15 IST):
- the real NSE answer is still stamped `21-Oct-2026 15:30`, about 13.7 hours after the close: a third observation;
- the reader refuses it for 22 Oct ("not today's session");
- read for 21 Oct, its NIFTY 50 and NIFTY BANK equal the official file (difference 0.00), and INDIA VIX differs by 0.02.

## Deviations and facts to know

1. **Size.** 502 lines of code including docstrings and imports, against about 270 estimated, and 481 lines of tests,
   against 340. The extra is the interfaces (four ABCs, each with one adapter) and the docstrings the rules ask for.
   No logic was added beyond the text.
2. **The raw file is the canonical JSON of the parsed answer, not NSE's own bytes.** The shared `PublicData.nse_json`
   returns the parsed answer. So the SHA-256 is of `json.dumps(sort_keys=True)`, and `source.py` says so. Keeping NSE's
   bytes would mean changing the shared client, which is outside A4h.
3. **The official file comes through `build_index_close_files`.** That is the copy archived in Drive, else NSE's own
   archive (the library looks in our stores first, then NSE; it never writes to Drive). So a confirm can happen before
   O6's job archives the file, and the values are NSE's either way. "No file in Drive yet" in the text means "no file
   anywhere yet".
4. **Worst-case run time.** The shared client itself tries 3 times (20 s timeout each, plus 1.5-4.5 s pauses), so one
   of my tries can take about 70 s. Worst case: 3 x 70 s + 2 x 60 s, about 5.5 minutes. That is inside O1's 600 s
   limit, but it is more than the "about 4 minutes" in the text.
5. **Hand runs outside O1 do not commit their receipts.** The Drive files are written, but committing
   `receipts/data/closes/` is the caller's step (O9). The 19:00 task that reruns the command must commit them, or the
   next O1 run's step commits them, since its pathspec matches.
6. **A receipt whose Drive file is gone** makes the confirm or the recheck raise (`json.loads(None)`), and O1 records
   the step failed and alerts. That is loud, not silent; I kept it rather than add a branch for a case O9's write order
   makes unlikely.

## Next

After your PASS: merge (pull, full suite on the merged tree, `check_numbers`, push), then tell O1/O2 and the FL1
builder. The go-live dates are for the orchestrator or owner to set. After go-live I report the first 5 sessions'
lines.

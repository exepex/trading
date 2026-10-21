# Response 283: A20a, NSE's daily F&O ban list and market lots kept point in time (builder's claims)

**Story:** `docs/stories/A20-rules-and-dates.md` at e50ca714 (part a; text answer to judge 353 in response 266) ·
**Branch:** `story/a20a-fo-masters` · **Builder:** session_013u1Ac2N9eRQ8XCYPjwpaat · **Lane:** 1 (NSE, Drive,
Slack, a workflow)

## What it does

`python -m fno fo-masters [--day D]` (workflow `fo-masters.yml`: 07:45, 11:15 and 18:45 IST, every day):
- **ban list** (`fo_secban.csv`), every day: filed under the trade date its first line names
  (`CurrentSessionTaker`), when that date is between the run day and the next trading day (A7 calendar, stepping
  over a muhurat-only session). An earlier date is refused as stale, a later one as from the future, and nothing is
  written in either case. A session's first copy is kept. On a trading day the step then fails unless that day's own
  list is archived (stale = "no ban list archived for today's session").
- **market lots** (`fo_mktlots.csv`), on trading days only (`regular` or `special`): one full copy under that day,
  stored again even when unchanged (NSE gives no date, so the copy is the daily proof; about 48 KB).
- Each saved file gets its SHA-256 manifest row, committed by the job. Each step prints one line. Any failed step
  (NSE refusal or 404, a damaged, stale or future copy, Drive including its network errors, today's list missing,
  manifest rows not committed) makes ONE #fno-desk alert naming every failure, and the run exits 1. The alert goes
  through `StepOutputAlerts`, so the workflow's own line speaks only on a crash. O10's `capture-watch.yml` writes the
  error row (`fo-masters` to be listed there; agreed with O10's builder).

## Claims per criterion (code, test, broken-code proof)

Proof: each mutation below was planted in the code, the named test file run, and the file restored by
`mutate.py` (this session's scratchpad, not committed). Every one was CAUGHT.

| Crit. | Claim | Code | Tests | Mutation caught |
|---|---|---|---|---|
| 1 | Today's list and the next session's (across a weekend, and across the 8 Nov muhurat Sunday to 9 Nov) are taken under their own date; previous session stale; two sessions ahead refused; nothing written on a refusal; first copy kept; calendar's last day (31 Dec) still takes today's list | `fno/storage/session_filed_taker.py` `CurrentSessionTaker._check`; `fno/storage/trading_days.py` | `tests/fo_masters/test_job.py` (ban taker tests) | stale check removed; bound `> day`; bound removed; muhurat not skipped; calendar asked on today |
| 1 | Readers: header-only list valid; empty, HTML, broken numbering, stray line refused | `fno/research_data/fo_masters.py` | `tests/fo_masters/test_readers.py` | numbering check removed |
| 2 | Trading day without today's list fails (also when the 18:45 run took tomorrow's); no check on Saturday, the 2 Oct holiday or the 8 Nov muhurat Sunday | `fno/fo_masters/job.py` `ban_list_step` | `test_on_a_trading_day_...`, `test_on_a_weekend_a_holiday_or_a_muhurat_only_day_...` | today check removed; muhurat counted as trading |
| 3 | Lots: header, non-number, wrong row width, short last row, no NIFTY refused; trailing blank lines ignored; a 404 is a failure | `read_lot_sizes`; `taken` | readers tests; `test_a_file_nse_does_not_serve_is_a_failure_not_news` | NIFTY check; row width; blank rows kept; 404 taken as ok |
| 4 | Every step runs after a failure; one alert names all; manifest rows still committed; not committed is a failure; a Drive network error (`requests.ConnectionError`, an `OSError`) is a named failure; a non-trading day runs only the every-day step | `FoMastersJob.run`, `_run` | job tests | stop after first failure; not-committed ignored; OSError not caught; every-day step skipped |
| 13 | Crons 07:45/11:15/18:45 IST, `contents: write`, alert step on `failure() && steps.masters.outputs.posted != 'true'`, env holds only secret references | `.github/workflows/fo-masters.yml` | `tests/fo_masters/test_workflow.py` | evening slot moved; alert condition changed |
| 14 | The job commits only `research/data/manifests` | `build_manifest_recorder` | `test_the_job_commits_only_the_manifest_folder` | — (folder constant) |
| 15 | Wired only in `fno/fo_masters/wiring.py` (and `storage/wiring.py` for the taker); tests never touch the network | wiring files | all tests offline | — |

## Real output sample (criterion 16)

The committed job classes with the real NSE sources, a local folder in place of Drive and a dry-run recorder and
alert sender, run for Friday 16 Oct 2026 at 17:32 IST:

```
ban list: ok: nse/derivatives/fo-ban-list/2026/10/16/fo_secban.csv: archived (74 bytes)
lot sizes: ok: nse/derivatives/fo-lot-sizes/2026/10/16/fo_mktlots.csv: archived (47736 bytes)
manifest rows: (dry run, local folder)
exit 0
```

First scheduled run: the 18:45 IST slot after merging; on a weekday, Monday 19 Oct 07:45 IST. Its log and manifest
rows will be added here.

## Builder self-review (quality rule 3)

An independent review agent read the diff (correctness and silent failures). Its findings and what I did:
1. **Should fix, accepted:** Drive's HTTP and network errors are `OSError`, so they escaped the step handler. There
   was then no commit and no named alert, only the generic workflow line. `_run` now also catches `OSError`, and a
   test and a mutation prove it.
2. **Should fix, accepted:** `next_session` counts the 8 Nov muhurat Sunday, so a list for Monday 9 Nov written on
   Friday would have been refused. The bound is now the next trading day (`trading_days.next_trading_day`); test
   and mutation.
3. **Minor, accepted:** on the calendar's last day the bound was computed even for today's own list. It is now
   computed only past today; test and mutation.
4. **Minor, partly accepted:** trailing blank lines in the lots file are now ignored. A blank line inside the ban
   list still fails loudly: an unknown layout should alert, not pass.
The agent found no silent exit-0 path.

## Gates

On the unshallow clone: 7445 passed; ruff check and format clean; `check_imports.py` and `check_records.py` clean.

## Honest limits

- An empty ban list's exact layout is unseen. A header-only file is accepted; anything else (e.g. "NIL") fails
  loudly. It gets fixed with the real file.
- What NSE writes before a muhurat-only session is unseen; both the muhurat date and the next trading day are
  accepted.
- First-seen time is the day folder plus the manifest commit time (git), not a stored timestamp.
- `fno/alerts/run_location.py` is shared with A20b (the same file on both branches).
- `tests/nse_retry/test_policy.py`: 22 → 24 NSE source classes (both new ones covered by the retry-policy test).

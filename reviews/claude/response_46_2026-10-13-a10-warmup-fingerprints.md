# Response 46: A10 2017-18 warm-up closes, and a fingerprint for every new file (builder's claims)

Status: **built; awaiting judge**. Story: `docs/stories/A-data-foundation.md`, section A10. Code commit `deeec72`
(merged as `bf045b9`/`de2e054`), claims commit after it.

## Two facts that change the story's wording (stated first)

1. **2018 alone cannot warm up F2.** The calendar gives 2018 only 245 daily sessions (261 weekdays, 16 weekday
   holidays; 7 Nov is muhurat only). With 1 Jan 2019 that is 246 previous India VIX closes, short of F2's 250. The
   calendar takes whole years, so 2017 is added too (its circular below). 2017-18 F&O files are never opened.
   Strong evidence (calendar counts: `2017 247 daily sessions, 2018 245 daily sessions`).
2. **The first 2019 decision day is 14 Jan 2019, not 2 Jan.** B2's own rule (`build_cycles`, `cycle_rows`) gives the
   first 2019 cycle as decision 2019-01-14, expiry 2019-02-28. I test both days: 2 Jan as the story asks (F1 priced on
   the 31 Jan monthly expiry) and 14 Jan as the real first decision. Strong evidence (output below).

## What was built

| Part | File | What it does |
|---|---|---|
| Calendar | `research/data/calendar/nse_sessions.csv` | 2017 rows from NSE/FAOP/33750 and 2018 rows from NSE/FAOP/36476 (official PDFs on nsearchives, each row linked), muhurat 2017-10-19 and 2018-11-07 |
| Index closes from 2017 | `fno/storage/raw_source.py:153` | `NseIndexCloseSource.first_day = 2017-01-01`; generic `day_for` (`:73`) reads the day back from any NSE file name |
| One manifest path | `fno/storage/manifest_folder.py` | `ManifestFolder` (`:43`): one CSV per dataset in `research/data/manifests/`, `write` (`:65`, whole) and `record` (`:72`, one row, never changed); `FingerprintingStore` (`:93`) writes the row in the same `put`, after the store accepted the bytes |
| Wiring | `fno/storage/wiring.py` | The owner's Drive store is wrapped in `FingerprintingStore` (`:79`); `coverage_datasets()` (`:156`) reads the manifests fresh; `LIBRARIAN_DATASETS` adds index closes (`:167`); laptop manifests no longer read |
| Coverage | `fno/storage/coverage.py` | `CoverageDataset.check` (`:40`) verifies SHA-256 and content, returns whether a row exists; unfingerprinted files listed and counted ("no sha"), result not complete (`:65`, `:134`, `:149`) |
| Librarian | `fno/storage/librarian.py` | Verifies through `CoverageDataset.check` (one verification path); `--from` defaults to each dataset's first day |
| Warm-up | `fno/research_data/warmup_closes.py`, `python -m fno nifty-warmup` | Builds `research/data/nifty-panel/warmup_closes.csv` (date, session, NIFTY 50, India VIX, file, SHA-256) from index-close files only; any session without both closes fails the build |
| Reader hook | `fno/research_data/panel_reader.py:93,97` | Warm-up sessions are added before the panel's first session as closes-only `SessionClose`s (no option or future rows), only when the panel's first year is read. **No B1 file was edited** (B1's `research_engine/` reads `panel.sessions_through` as before) |

## Criteria

**1. The 2017-18 index-close dataset is complete in Drive, 0 missing, 0 damaged, every file fingerprinted.** MET
(strong evidence: live runs).
- Librarian run: `nse/indices/index-close 2017-01-01 to 2018-12-31: 494 sessions, 5 already there and verified, 489
  uploaded, 0 with a sourced exception` / `result: complete` (the 5 came from a one-week smoke test of the same path).
- `python -m fno data-coverage --to 2026-10-12`:
  ```
  dataset                                    from         to expected present missing damaged no sha
  nse/derivatives/fo-bhavcopy-legacy   2019-01-01 2024-07-05     1367    1366       0       0      0
  nse/derivatives/fo-bhavcopy          2024-01-01 2026-10-12      690     690       0       0      0
  nse/indices/index-close              2017-01-01 2026-10-12     2423    2423       0       0      0
  nse/derivatives/participant-oi       2019-01-01 2026-10-12     1929    1929       0       0      0
  excepted nse/derivatives/fo-bhavcopy-legacy 2021-03-30: ... (A1's sourced exception)
  result: complete
  calendar sha256 e34fbad752bb244e6116c1e474902208a72a03f5af6037c6d75bf9baa6756b4d
  ```
  No "unexpected file" line: no index-close file exists on a day the new 2017-18 rows call closed (an independent
  check of the circular rows against NSE's data).

**2. F2 on the first 2019 decision day, and F1 where its legs traded, equal hand calculations.** MET for 2 Jan 2019
(strong evidence); see fact 2 for 14 Jan.
- Values (real panel and warm-up file):
  ```
  2019-01-02 VIX 16.39 median prev 250 14.25  F2 True F1 -0.04516646575232386 | without warm-up: F2 None F1 None
  2019-01-14 VIX 16.16 median prev 250 14.415 F2 True F1 None                 | without warm-up: F2 None F1 None
  ```
- Tests: `tests/test_warmup_closes.py:126` (F2 on both days equals `today > median(previous 250 non-muhurat closes)`
  built by hand from the CSV rows and the panel's 2019 closes), `:132` (F1 on 2 Jan 2019: realised part recomputed by
  hand from the 21 closes, `F1 == implied - realised`; the implied part is B1's own Black-76 solver, not re-derived),
  `:142` (F1 on 14 Jan 2019 is `None` only because the ATM 10750 put of 28 Feb 2019 had volume 0 that day; the 21
  closes are there).
- For the judge's recomputation: India VIX closes are in `research/data/nifty-panel/warmup_closes.csv` (column `vix`,
  drop the two `muhurat` rows) plus 2019-01-01 (15.33, the panel's `vix` for that day): median of the last 250 = 14.25.

**3. An archived file with no manifest row is reported and the result is not complete; a saved file gets its row in
the same operation.** MET (strong evidence).
- Tests: `tests/test_coverage.py:136` (planted: present 5, `unfingerprinted == [2019-01-04]`, "no sha" column 1,
  result INCOMPLETE); `tests/test_fingerprints.py:50` (a saved file's row written by the same `put`; a row is never
  changed), `:63` (a refused save writes no row; a file of no known dataset is never saved).
- Real check on Drive (manifest copy with the 2018-12-27 row removed):
  ```
  nse/indices/index-close              2018-12-01 2018-12-31       20      20       0       0      1
  no fingerprint (content checked only) nse/indices/index-close 2018-12-27
  result: INCOMPLETE: missing, damaged or unfingerprinted files above
  ```
- Real save path: all 494 rows for 2017-18 in `research/data/manifests/index-close.csv` were written by
  `FingerprintingStore` as the librarian saved each file; each equals the `index_sha256` of the warm-up file (0
  mismatches in 494).

**4. The current-format F&O manifest covers every session to the latest archived day, from the same code, and the
laptop copy is no longer read.** MET (strong evidence).
- `research/data/manifests/fo-bhavcopy.csv`: 690 rows, 2024-01-01 to 2026-10-12, written by `data-fingerprints`
  (`ManifestFolder.write`); coverage above shows 690/690 with 0 "no sha" (the 12 Oct file is now fingerprinted).
- `grep -rn "nse_raw_download\|manifest.csv\|manifest_participant" fno` finds nothing: the code reads only
  `research/data/manifests/`. The regenerated manifests agree with the laptop tool's independent NSE downloads:
  `fo-bhavcopy: both 689, differ 0, drive only [12 Oct]`; `participant-oi: both 1929, differ 0`.
- New days get their row when saved (`FingerprintingStore` wraps every Drive upload, including `RawFileLibrary`'s
  archive).

**5. No 2017-18 F&O option or futures data is read by experiment code.** MET (strong evidence).
- Test `tests/test_warmup_closes.py:110`: the panel loaded the way experiment code loads it (`load_research_data`)
  starts its sessions on 2017-01-02, but its earliest option and future rows are 2019-01-01, and `build_cycles`' first
  decision day is 2019-01-14 (warm-up days never become decision days: cycles come from option expiries, which
  warm-up days do not have). `:103`: every warm-up row names an `ind_close_all_` file, never an F&O file. The F&O
  sources' `first_day` stays 2019-01-01, so no command fetches 2017-18 F&O files.

**6. Code size, lint, imports, tests; raw files only in Drive.** MET.
- `python -m pytest -q`: 818 passed. `ruff check fno tests tools`: all checks passed. `python tools/check_imports.py`:
  clean. `python tools/check_records.py`: clean. Largest touched files: `wiring.py` 235 lines, `coverage.py`
  151, `manifest_folder.py` 113.
- Committed data are derived only (manifests, warm-up closes: 494 rows of two numbers); the 494 raw index-close files
  are only in Drive.

## Doubts and limits

- **F1 is `None` on experiment 1's first 2019 cycle (14 Jan 2019)** because the ATM Feb put did not trade. That is a
  property of the data, not of the warm-up; B5 should expect fewer F1 decisions early in 2019. Strong evidence.
- **2017 index closes are archived but only the last 250 matter** for F2. The extra year costs nothing to keep and
  follows the calendar's whole-year rule.
- **Unscheduled changes in 2017-18** (a holiday added after the circular) would show as missing or unexpected files;
  coverage shows none, so I found no such change. Some evidence (absence of a contradiction).
- **Manifest rows are written to the repository working tree** when files are saved; the session that saves must
  commit them. The librarian does not remind it. A saved file whose row is never committed shows as "no sha" in a
  fresh checkout, so the failure is loud, not silent.
- `fno/research_data/panel_reader.py` (A3's reader) gained the warm-up hook; B1's files are untouched.

## Judge 34 minor 1: manifest rows written at save time are now committed (fixed)

Accepted: the judge is right. Before this fix nothing committed the rows, and my claims only said so as a doubt.
- Code: `fno/storage/manifest_commit.py`. `ManifestRecorder` is the interface; `GitManifestRecorder` commits only
  `research/data/manifests/`, then runs `git pull --no-rebase --no-edit origin <branch>` and `git push origin HEAD`.
  The repository's hooks run (record scan on, never `--no-verify`). A failed step returns
  `manifest rows NOT committed: <step> failed: <reason>`. `run_librarian` (`fno/storage/librarian_cli.py`) commits in a
  `finally`, so a finished run, a source outage and a refused sign-in all commit what was written.
  `python -m fno data-coverage` (`fno/cli.py`, `uncommitted_lines`) lists every manifest file still uncommitted and
  exits 1. Wired in `fno/storage/wiring.py` (`build_manifest_recorder`).
- Tests: `tests/test_manifest_commit.py`, run against a real temporary git repository with a bare origin.
  - `test_a_save_without_a_committed_row_is_reported_until_it_is_committed_and_pushed`: data-coverage's line until the
    commit; the row is then on origin; a second commit finds nothing to do.
  - `test_only_the_manifest_folder_is_committed`: someone else's staged file is left staged.
  - `test_a_refusing_hook_is_reported_and_never_bypassed`: the hook's message is printed and the row stays pending.
  - `test_the_librarian_commits_its_rows_even_when_the_run_stops`.
- Real check: `uncommitted_lines(build_manifest_recorder())` on this repository gives `[]` (every row written so far
  is committed).
- Doubt (reasoning only): the push happens inside the command. If the session that runs it has no push rights, the
  outcome line says `push failed` and the rows stay committed locally. data-coverage on another checkout would then
  show "no sha", which is loud, not silent.

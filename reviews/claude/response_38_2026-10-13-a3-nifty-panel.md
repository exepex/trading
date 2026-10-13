# Response 38: builder's claims for story A3 (NIFTY option-chain panel)

Story: `docs/stories/A-data-foundation.md#a3-nifty-option-chain-panel`. Status: built 13 Oct 2026, awaiting the judge
(`docs/JUDGE.md`). Depends on A1 (calendar and exceptions on main; coverage run still in progress) and A2
(`fno/fo_bhavcopy.py`, reused unchanged).

## What was built

| File | What it does |
|---|---|
| `fno/research_data/nifty_panel.py` | `build_nifty_panel(...)`, `NiftyPanelBuilder` (days from the calendar, format precedence, research-ready gate, row extraction), `DailyFiles` (one dataset's day -> file), `cents`/`whole` (copy values, refuse rounding), `summary_lines` |
| `fno/research_data/panel_store.py` | `PanelSink` interface and `CsvGzPanelFolder` (yearly `options_<year>.csv.gz` + `manifest.json`, deterministic, swapped in only on success) |
| `fno/storage/wiring.py` | `daily_files`, `build_nifty_panel_files` (UDiFF first, then old format, plus index closes, each through a `RawFileLibrary`: stores, then NSE), `build_panel_sink`, `build_session_calendar`, `build_file_exceptions`, `PANEL_FOLDER` |
| `fno/cli.py` | `python -m fno nifty-panel --to YYYY-MM-DD [--from 2019-01-01] [--raw-folder FOLDER]`; exit 1 and nothing written when not research-ready |
| `fno/constants.py` | `PANEL_FORMAT_UDIFF/LEGACY`, `PANEL_INDEX_CLOSE`, day statuses, `NIFTY_SYMBOL`, `INDEX_OPTION` |
| `tests/research_data/test_nifty_panel.py` | 19 tests; fixtures `tests/fixtures/nse_panel/raw/...` are small real subsets (rows copied unchanged) of the Drive files for 2019-01-02, 2019-10-27 (muhurat Sunday), 2020-02-01 (Budget Saturday), 2024-01-02 (both formats), 2024-03-02 (DR-site Saturday, both formats) |
| `research/data/nifty-panel/` | The panel, 2019-01-01 to 2026-10-12, and its README |
| `research/2026-10-13-nifty-panel/` | `check_panel.py` (independent per-day check against the raw files), `compare_extract.py` (criterion 10), their result files and README |

## Acceptance criteria

| # | Criterion | Code | Test / evidence | Result |
|---|---|---|---|---|
| 1 | Rows per day = NIFTY option rows in the source file; manifest has the source SHA-256 | `nifty_panel.py:147-162` (`_rows`: every `IDO`/`NIFTY` record), `:108` (`fo_sha256`), `:124` (`rows`) | `test_each_day_has_every_nifty_option_of_its_file_with_both_files_fingerprinted` (5 fixture days, raw rows counted with plain `csv`); whole panel: `check_panel.py` re-counts all 1,928 days from the raw files: 0 problems | MET |
| 2 | 2024 before 6 Jul uses UDiFF (`udiff`); 2019-2023 old format (`legacy`) | precedence `nifty_panel.py:127-133`, order `wiring.py:118-124`; dates covered from the source classes (`DailyFiles.covers`, `:55`) | same parametrised test (2024-01-02, 2024-03-02 -> `udiff`; 2019/2020 days -> `legacy`); built manifest: every 2024-2026 day `udiff`, every 2019-2023 day `legacy` | MET |
| 3 | Same raw files, byte-identical outputs | `panel_store.py:84` (gzip `filename=""`, `mtime=0`), `:114` (sorted JSON, no build time), fixed `PANEL_COLUMNS`, row sort `nifty_panel.py:161` | `test_same_raw_files_give_byte_identical_outputs` (also asserts the gzip header has no time or name: a mutation to `mtime=None` makes it fail); real data: two full builds into two folders, all 9 files identical (SHA-256 below) | MET |
| 4 | Day with no F&O file: absent and listed as "no file" | `nifty_panel.py:105-107`, `:135-145` | `test_a_session_without_a_file_but_with_a_sourced_exception_is_left_out_and_listed` (2021-03-30); real build lists 2021-03-30 as `no file` with its exception | MET |
| 5 | `underlying` = NIFTY 50 close, `vix` = India VIX close | `nifty_panel.py:148` (both from that day's index-close file, for every row and both formats) | `test_rows_copy_the_raw_values_with_the_index_close_and_vix_of_the_day`; `check_panel.py` checks every row of every day against the raw index file: 0 problems | MET |
| 6 | (date, expiry, strike, type) unique; a duplicate fails the build | `nifty_panel.py:154-158` | `test_a_duplicate_contract_fails_the_build`, `test_rows_are_sorted_and_contracts_unique` | MET |
| 7 | Manifest: per day SHA-256 of the F&O file and the index-close file | `nifty_panel.py:108`, `:113` | test of criterion 1 compares both hashes with the fixture bytes; `check_panel.py` re-hashes both raw files for all 1,928 days | MET |
| 8 | Research-ready gate: fails naming days when a session lacks F&O file, NIFTY 50 or VIX close, unless sourced exception; never writes empty values | gate `nifty_panel.py:92-101`, `:110-118`, `:135-145`; empty range refused `:176-177`, nothing written on failure `:180-185` + `panel_store.py:117-121` | `test_a_session_without_a_file_or_exception_fails_the_build_naming_it_and_writes_nothing` (previous panel left untouched), `test_no_index_file_fails_and_never_leaves_underlying_empty`, `test_an_index_file_without_india_vix_fails`, `test_values_are_copied_never_rounded`; CLI exit 1 (`cli.py:40-52`) | MET |
| 9 | Deterministic, tested precedence: both formats -> current format, choice recorded | `nifty_panel.py:127-133`; manifest `source_format` and `fo_file` | `test_current_format_wins_on_a_day_with_both_and_the_old_one_is_the_fallback` (fails under a reversed loop: mutation checked) | MET |
| 10 | 2024-2026 rows reproduce the existing extract | - | `compare_extract.py`: 249,958 of 249,958 extract contracts found, 0 differences in close, settle, volume, open interest and underlying; 689 = 689 days (`compare_extract.json`) | MET |

Special sessions (orchestrator note): included and tested from the real calendar: muhurat 2019-10-27, Budget Saturday
2020-02-01, DR-site Saturday 2024-03-02 (manifest `session` = `muhurat`/`special`), and
`test_only_sessions_are_asked_for_and_nothing_is_written_to_drive` shows a Saturday and a holiday are never asked for.
The fake Drive in every test fails on any write. The real build holds all 6 special and 7 muhurat sessions of 2019-2026-10-12 (manifest `session` counts: 1,916 regular, 6 special, 7 muhurat).

## Command output (13 Oct 2026)

```
$ python -m fno nifty-panel --from 2019-01-01 --to 2026-10-12 --raw-folder <local read-only copy of Drive raw/>
NIFTY panel 2019-01-01 to 2026-10-12, calendar sha256 6101c8746fe17926498fbfcac895b7aad5218c4653982bba82337b6b5dea3961
options_2019.csv.gz: 773,364 rows, sha256 153d79b7abdef573dc4ec219f80762cbd1d8abe72114baffcc90deba4661dc02
options_2020.csv.gz: 736,996 rows, sha256 12b5874fbe7532e6025dd2228df2d68ec261819f89313c3ab1c57713b1d6495b
options_2021.csv.gz: 510,565 rows, sha256 121b5990621d3904399e099df6c7bbc8adad6f6d215429a6c552a9f29a003dbd
options_2022.csv.gz: 562,041 rows, sha256 5c9a49787f5d1c91d9c127bed4c2e22050e26d44aab25ca55f860696f39c8af2
options_2023.csv.gz: 340,423 rows, sha256 639181a8ef7626d087ed60edecaee129436e05a30c4de5a6c344d2370013aafb
options_2024.csv.gz: 398,739 rows, sha256 f602c87779aad17f5fc1360e552a958ff10a2c967d467d7f32205c5ee0877053
options_2025.csv.gz: 395,866 rows, sha256 26e20e6ed7532cc48b5206a5f596cdf974e9cd407df3e98a78867bcdc8f51972
options_2026.csv.gz: 340,704 rows, sha256 467bac0e4ba26ded589cb3a8f7600d645ce05c9cdb33fda5de3fa986deb631c3
sessions: 1 no file, 1928 ok
left out 2021-03-30: no file (... NSE's archive has no old-format F&O bhavcopy for it: 404 from both archive hosts ...)
(21 min 50 s)
second build into another folder: manifest.json 9589f7a8...e77f and all 8 option files identical (sha256sum + diff)
$ python research/2026-10-13-nifty-panel/check_panel.py <raw copy>   -> 1928 days checked, 0 problem(s)
$ python research/2026-10-13-nifty-panel/compare_extract.py          -> 249958/249958 found, 0 differences, 689 = 689 days
$ python -m pytest -q                       -> 414 passed in 35.65s
$ ruff check fno tests tools                -> All checks passed!
$ python tools/check_imports.py             -> clean: 102 files, 1 archival skipped
$ python tools/check_records.py             -> record scan: clean (306 files)
```

How the build read the raw files: a scratch script copied the 3,984 needed files from Drive read-only (`GoogleDriveStore.get`
only) into a local folder; the command then read them through `RawFileLibrary` (local copy, then Drive, then NSE).
Building straight from Drive works (`--raw-folder` omitted) but needs about one Drive request round per file
(~1 file/s, over an hour).

## Size (orchestrator's limit: about 50 MB per file, several hundred MB in total)

| Year | Sessions | Rows | .csv.gz |
|---|---|---|---|
| 2019 | 245 | 773,364 | 7.8 MB |
| 2020 | 252 | 736,996 | 7.8 MB |
| 2021 | 247 | 510,565 | 5.7 MB |
| 2022 | 248 | 562,041 | 6.3 MB |
| 2023 | 246 | 340,423 | 4.1 MB |
| 2024 | 249 | 398,739 | 4.8 MB |
| 2025 | 249 | 395,866 | 4.9 MB |
| 2026 (to 12 Oct) | 192 | 340,704 | 4.3 MB |
| **Total** | **1,928** | **4,058,698** | **45.6 MB** + manifest 0.7 MB |

Largest file 7.8 MB, total 46.3 MB: inside the limit, so it is committed.

## Doubts and limits (stated, not hidden)

1. **Signature differs from the story's text** (reasoning only, design choice): the story writes
   `build_nifty_panel(fo_libraries, index_library, start, end) -> Panel`. The built function adds keyword arguments
   `calendar`, `exceptions` (criterion 8 needs both) and `sink` (the output store behind the `PanelSink` interface,
   CLAUDE.md "every store behind an interface"). `fo_libraries` are `DailyFiles`, each wrapping a `RawFileLibrary` with
   its source's file naming (wired in `wiring.py`), so the panel never knows NSE's naming or Drive.
2. **NIFTY futures not built.** The scope says "(and NIFTY futures for reference)" but no criterion and no output
   schema covers them, and the orchestrator said not to add fields. If wanted, a separate `futures_<year>.csv.gz` with
   its own schema is a small follow-up; it needs a decision on the columns.
3. **2021-03-30 is a real session with no NIFTY option prices** in the panel (no old-format file at NSE). Anything
   that needs every day (B2 cycles, marks of open positions) must treat it as a gap, not a holiday. NSE's F&O
   market-activity zip for that day (the exception's source) may hold some option data; not checked (reasoning only).
4. **A Drive gap for A1:** `raw/nse/indices/index-close/2021/03/ind_close_all_30032021.csv` is missing on Drive, but
   NSE serves it (HTTP 200, 8,474 bytes, checked 13 Oct 2026). Not used by the panel (the F&O file is missing that day),
   but A1's coverage should report it unless it has an exception. Strong evidence (direct requests).
5. **Git growth if rebuilt often** (strong evidence, arithmetic): each rebuild that adds days rewrites the current
   year's file (4-5 MB) and the manifest (0.7 MB); a daily commit would add about 1.2 GB of history per year.
   Recommendation: rebuild and commit only when research needs new data (for example monthly or before an
   experiment), or keep the current year outside git. Decision for the orchestrator/owner.
6. **gzip bytes depend on the zlib version** (some evidence: gzip output is stable for a given zlib and level, not
   guaranteed across versions). The manifest therefore also records each file's uncompressed `csv_sha256`; a judge on
   another machine should compare that if the `.gz` hashes differ.
7. **Stale prices are in the panel by design:** contracts that did not trade keep NSE's close (often the previous
   close). Research must filter on `volume` (as response 3 found); the panel copies, it does not judge.
8. **Challenge data is now in the repository:** the panel holds 2019-2023, the challenge period of experiment 1.
   Building and checking it reads no strategy result, but any agent can now read it before B5's freeze. The guard is
   the ledger (B4), not file access (reasoning only).
9. `--to` has no default on purpose: "the last available day" must be stated, since a session without files fails
   the build.

## Judge 14 (FAIL, 1 should-fix, 6 minors): answers

Verdict: `reviews/judge/judge_14_a3_nifty_panel.md`. Orchestrator decisions of 13 Oct 2026: build the futures file
(finding 1); fix minors 2, 4 and 5; minor 3 is fixed on main in 769878d; minor 6 is known and stays as is. The
panel was rebuilt with all changes; **the SHA-256 values in "Command output" above are superseded by the ones below.**

| # | Finding | Answer | Proof |
|---|---|---|---|
| 1 | Should fix: futures in scope, not built | **Fixed.** New `futures_<year>.csv.gz`: every listed NIFTY index future (`IDF`/`FUTIDX`), columns `date, expiry, close, settle, volume, open_interest, underlying, source_format, session`; same deterministic writing; manifest `futures_rows` per day and file entries; a session without NIFTY futures, or a future listed twice, fails the build. Story text updated to match (`docs/stories/A-data-foundation.md`, A3 expected design) | Code: `fno/research_data/panel_rows.py:41-67` (both tables from one pass; `_add` refuses duplicates), `nifty_panel.py:106-109` (gate, counts), `panel_store.py:69-100` (`YearlyGzTable` per table). Tests: `tests/research_data/test_nifty_panel_futures.py` (`test_each_day_has_every_nifty_future_of_its_file_...` on all 5 fixture days counted from the raw file, `test_future_rows_copy_the_raw_values`, `test_a_day_without_nifty_futures_fails_the_build`, `test_a_duplicate_future_fails_the_build`); determinism test now covers both tables. Rebuild check: `check_panel.py` also recounts futures per day from the raw files and checks their underlying and session: 1,928 days, 0 problems. Real data: 3 futures on every one of the 1,928 sessions, 5,784 rows |
| 2 | Minor: a partial-range build deletes other years | **Fixed by refusing.** `PanelSink.begin(start, end)` runs before any file is read; `CsvGzPanelFolder.begin` raises `PanelRangeError` when the range starts later or ends earlier than the existing manifest's; extending is allowed; the CLI exits 1 with the reason. Merging untouched years was not chosen: a range cutting a year in half would still lose that year's other days (reasoning only) | `panel_store.py:106-116`, `nifty_panel.py:145`, `cli.py:53`. Tests: `test_a_build_that_would_drop_days_is_refused_and_changes_nothing` (later start and earlier end, all files byte-identical after), `test_a_build_may_extend_the_panel_and_keeps_every_year`, `test_the_command_refuses_a_narrower_range` |
| 3 | Minor: Drive store has no retry | Fixed on main by the orchestrator (769878d); included in this push | merged before this change |
| 4 | Minor: `settle` on expiry day | **Fixed, and the judge's statement corrected with data.** Measured on every expiry-day row of the build: from 6 Feb 2020 on, an expiring option's `settle` equals that day's Nifty 50 close; up to 30 Jan 2020 it is 0.00. So it is not only a UDiFF matter (2020-2023 old-format files carry it too). README warning added | per year: 2019 all 7,868 rows 0.00; 2020 714 rows 0.00 (to 30 Jan) and 10,161 = index close (from 6 Feb); 2021-2026 all = index close. `research/data/nifty-panel/README.md`, "On its expiry day" |
| 5 | Minor: muhurat closes not marked on rows | **Fixed.** New last column `session` (`regular`, `special`, `muhurat`) on both tables, from the calendar; README explains muhurat closes | `panel_rows.py` (row tuples), tests: every fixture day's options and futures carry their session (`test_each_day_has_every_nifty_future_..._and_every_row_its_session_kind`); `check_panel.py` checks the session of every row of every day |
| 6 | Minor: merge commit ee29335 without trailer | Known; left as is (orchestrator). Merges now use `git fetch` + `git merge -m` with the trailer | - |

Structure: row extraction moved to a new module `fno/research_data/panel_rows.py` (67 lines) so the builder stays
small (`nifty_panel.py` 168 lines, `panel_store.py` 152); the tests' shared fixtures moved to
`tests/research_data/panel_fixtures.py`.

### Command output after the fixes (13 Oct 2026)

```
$ python -m fno nifty-panel --from 2019-01-01 --to 2026-10-12 --raw-folder <local read-only copy of Drive raw/>
futures_2019.csv.gz: 735 rows, sha256 085e92fb5409dade2e58bfd0027c2313c9064781a39c3e38ec4b29efe8739c89
futures_2020.csv.gz: 756 rows, sha256 899beb08590c4df740235ec610b8ef12027ee08d81d7c0e1fead981ddc2179d4
futures_2021.csv.gz: 741 rows, sha256 ccb6252317069b2f7d1e0fe3ddfc65b1a5159c861209bf273df4210c133d24f4
futures_2022.csv.gz: 744 rows, sha256 3c068591861ad7427bc05d9b0ecf8d33e36d511c7a9b23b37b9599256d647d5b
futures_2023.csv.gz: 738 rows, sha256 531cfd75040677fde51490d126d242882a9bec33bfc9a3726ae1930abefa6170
futures_2024.csv.gz: 747 rows, sha256 cf9484633ae103e71ca8de983c1ca25c97be9f044648bb82c7cc1964184a6c3c
futures_2025.csv.gz: 747 rows, sha256 cc4244fda7692ea4792a72109a681a65e87d0baadf59d03a1645748075caaf4a
futures_2026.csv.gz: 576 rows, sha256 4e08686ff29c60e0c5691350ec8015ee59d03304166fcb3bd7369738b9fa7644
options_2019.csv.gz: 773,364 rows, sha256 6f7888acf91ad98d6cda57c43a59b4baa2f30e18559728e84eaf4299e48cb9a9
options_2020.csv.gz: 736,996 rows, sha256 6ef42455e676c37f2d2afefda3c0ed3c5b95a6cc9dc530d66aeb179fae8cc56a
options_2021.csv.gz: 510,565 rows, sha256 a71f743c748d0c11fd0d3a61835bcb596c42af1d93442825fa730bd2e588ca3d
options_2022.csv.gz: 562,041 rows, sha256 865a79785812fa2c280a1445e12717a204aef4997143af618cc9331dd2c51744
options_2023.csv.gz: 340,423 rows, sha256 6934492c5fabbc4efc92b0016281c0038b1ef8f6f35337fc3d1cea7f4b9c5fe2
options_2024.csv.gz: 398,739 rows, sha256 d736337ec69b96eda8ffebf8337e25bdd70fa1e0e4c4051e5c469cac13cee15f
options_2025.csv.gz: 395,866 rows, sha256 829ac6aed10d069a579e9628dc014555a2f20c6c4a0d39f72a57033ef45d3b43
options_2026.csv.gz: 340,704 rows, sha256 b48a401139c8f03ab087ca4090b1fadcda0fe3de1bbc1034f0426be3a54073ac
sessions: 1 no file, 1928 ok        (23 min 49 s)
second build into another folder: all 17 files identical (manifest.json 89a06376...7636)
$ python research/2026-10-13-nifty-panel/check_panel.py <raw copy>   -> 1928 days checked, 0 problem(s)
$ python research/2026-10-13-nifty-panel/compare_extract.py          -> 249958/249958 found, 0 differences, 689 = 689 days
$ python -m pytest -q                       -> 540 passed
$ ruff check fno tests tools                -> All checks passed!
$ python tools/check_imports.py             -> clean: 119 files, 1 archival skipped
```

Option row counts are unchanged from the first build; the option files' bytes changed only because of the new
`session` column. Size now 46.7 MB in total (options 45.8 MB, futures 0.1 MB, manifest 0.8 MB); largest file 7.9 MB.

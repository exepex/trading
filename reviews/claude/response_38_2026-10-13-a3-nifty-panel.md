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

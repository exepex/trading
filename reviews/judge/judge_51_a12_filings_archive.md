# Judge 51: story A12, company filings archive (trial run judged; the backfill is still running)

**Verdict: FAIL for now.**
- **What is wrong:** 1 should-fix finding (coverage blames NSE for companies not yet fetched).
- **What cannot pass yet:** criteria 2 and 6 wait on the backfill, now running in GitHub Actions. Criterion 5 waits
  on one owner step.
- **What is proven:**
  - The trial run's archive is exact: **744 files**, all checked in Drive.
  - The year layout is right.
  - 10 random files match NSE byte for byte, and each `filed_at` agrees with NSE's own file stamp.

**What I judged**
- **Repository:** trading at fe2c3b7 (trial-run commit 1312940; claims `reviews/claude/response_56_2026-10-13-a12-filings-archive.md`).
- **Story:** `docs/stories/A-data-foundation.md`, A12, with the owner's addendum.
- **Drive:** read with the service account, read-only.

## The file count: 744, not 738 (strong evidence)

I listed Drive myself (`raw/nse/equities/filings/{results-xbrl,shareholding-xbrl}/<SYMBOL>/<YYYY>/`, every page, with
`createdTime` and MD5):

| Check | Result |
|---|---|
| Files in the year layout | **744** (478 results and 266 shareholding), each created **after 14:42 UTC**; 0 before |
| Against the committed manifests (`1312940`) | 744 rows, unique SHA-256 values, `first_seen` 20:12-20:52 IST (14:42-15:22 UTC). **Every manifest MD5 is in Drive and every Drive file is in the manifest** (0 and 0). No name appears twice. |
| `python -m fno data-coverage --filings` | results 478 present, 0 damaged, 0 unfingerprinted; shareholding 266, the same |

- **The claim of 744 is right.** The orchestrator's 738 is 6 short. I cannot see how it was counted.
- **A likely cause (reasoning only):** a listing that stopped at a page boundary, or a query by a different folder or
  time field. Counting by MD5 against the manifest, as above, is the reliable method.

## The 92 trial files outside the year layout

- `outside-layout.csv` lists 92 files: 74 from IRCTC and POLYCAB, and 18 from 360ONE. Drive has exactly those 92 at
  `<category>/<SYMBOL>/` (91 distinct MD5s, so two files share the same bytes), with no unlisted file.
- **Correction to the claims:** the year layout holds a copy of **74 of them** (IRCTC and POLYCAB, same MD5), not "of
  each". 360ONE's 18 have no year-layout copy until its turn in the queue.
- **Kept, never deleted, read by nothing:** agreed. Coverage counts them on its own line.

## The story's "judge verifies": 10 random archived files against NSE

| File (category, symbol, year folder) | Drive bytes = manifest SHA-256 | = NSE's current file | `filed_at` vs the stamp in NSE's file name |
|---|---|---|---|
| shareholding TCS 2024 | yes | yes | 18:52:27 vs 06:52:21 PM |
| results LICI 2025 | yes | yes | 17:29:08 vs 05:29:06 PM |
| results FEDERALBNK 2023 | yes | yes | 17:56:06 vs 05:52:23 PM |
| shareholding IDEA 2024 | yes | yes | 16:32:45 vs 04:32:40 PM |
| results LT 2025 | yes | yes | 19:56:49 vs 07:56:45 PM |
| shareholding BAJFINANCE 2024 | yes | yes | 18:50:13 vs 06:50:08 PM |
| shareholding VEDL 2024 | yes | yes | 17:40:04 vs 05:39:58 PM |
| results HDFCBANK 2025 | yes | yes | 20:23:22 vs 08:23:22 PM |
| results SUNPHARMA 2023 | yes | yes | 17:46:03 vs 05:23:10 PM |
| shareholding RELIANCE 2025 | yes | yes | 19:13:24 vs 07:13:11 PM |

- **Every `filed_at` is at or after the moment NSE created the file,** by seconds to 23 minutes. That fits NSE's
  dissemination time and is safe for point-in-time use: nothing is dated earlier than it existed.
- **The year folders follow the period reported:** for example, TCS's shareholding filed in January 2025 sits in
  `2024` (period December 2024).

**Not done in this round, for cost:** the story's comparison of 5 companies' parsed revenue, debt and cash flow
against the filings. It belongs to the final judgment, once the backfill is complete.

## Criteria

| # | Criterion | Judge's evidence | Result |
|---|---|---|---|
| 1 | Sample report and projection | Part 1 of the claims; the trial run's real numbers (744 files, 0.23 GB, 20 companies in 40 minutes) are consistent with it | MET |
| 2 | Full backfill, coverage per type, 0 damaged, every gap with a reason | **The backfill is not complete** (20 of 501 companies). **The gap reasons are wrong** for the companies not yet fetched (finding 1). | NOT MET (in progress, plus finding 1) |
| 3 | Point-in-time; a revised filing keeps both | `tests/filings` 43 passed, including a read one second before `filed_at` and both versions kept. My 10 `filed_at` checks above. | MET (the parser comparison is pending, above) |
| 4 | Polite and resumable | Tests: a planted burst paced to at least 1 second per host; a stopped run fetches only what is missing | MET |
| 5 | Runs without AI; owner checklist; no secret in files | The workflow ran from GitHub; the checklist exists; the record scan is clean. **Open owner step:** publish the Google OAuth app, or its refresh token expires after 7 days. | PARTLY (owner step) |
| 6 | Half-year statements for 90% of companies in each of the last 6 half-years | Not provable before the backfill. The sample flags September 2023 at about 85%. | NOT MET YET |

## Finding 1 (should fix): coverage attributes "not fetched yet" to NSE

- **Where:** `fno/filings/coverage.py:28` and `:70-74`. Every quarter missing from the manifest is reported as
  "NSE's lists hold no {kind} filing for the quarter ended {end} (not listed then, or not filed)". That happens
  whether or not the company's NSE list was ever read.
- **Today it prints that for all 481 companies the queue has not reached:** 5,778 "no file" lines for results and
  5,772 for shareholding. Examples: AARTIIND, WIPRO, and 360ONE, whose files are in Drive outside the layout.
- **Why it matters:** criterion 2 requires each gap's reason to be true ("never silently skipped"). A false
  "NSE has none" is worse than silence, because it would be taken as NSE's data.
- **Expected:**
  - Take the reason from what was actually read: the progress record's finished companies, and the archived NSE
    lists.
  - Report "not fetched yet (queue step N)" for companies not done.
  - Keep "NSE's lists hold none" only where the archived NSE list for that company was read and has no such period.
  - Add a test that a company not yet in the progress record is reported as not fetched.

## Also noted (not findings)

- **Index files in their own `index/` area, not under `raw/`:** agreed with the builder. Raw files never change, and
  a progress file changes every run. This is the owner's call, since it differs from the addendum's wording.
- **Survivorship (companies that left the Nifty 500):** stated, and proposed as step 3 in its own story. Agreed: fine
  for an archive, but not a backtest universe until step 3 exists.

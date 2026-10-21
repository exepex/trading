# A23. FII/DII flow history, 2019 on: NSE's FII derivatives statistics and participant-wise trading volume

**Repository:** trading · **Lane:** 1 (new story; NSE, Drive) · **Branch:** `story/a23-flow-history` · **Builder:**
session_013u1Ac2N9eRQ8XCYPjwpaat · **Orchestrator:** session_01VG1RqxLFUVdvvPuMRYZtDH · **Judge:** Judge F

**Description:** As the statistician and the F&O trader, I want daily FII and DII flow figures from 2019, each dated by
when it became public, so GR1 or a later study can test whether flows sharpen the NIFTY and BANKNIFTY ranges before
anything live uses them.

**Context:** owner-approved task (DESK_DECISIONS 2f1e3b63, 21 Oct 2026). `docs/DATA_USE_MAP.md`: FII/DII cash and
NSDL FPI flows have 6 sessions of history (P8 captures only NSE's and NSDL's latest day), so nothing can test them.

## Step 0 (21 Oct 2026, 21:00 IST, from this container) [strong: direct reads]

| Data | Source | History read | Point in time | Terms |
|---|---|---|---|---|
| **FII derivatives statistics**: FII buy and sell (contracts and crores) and end-of-day OI for index futures, index options, stock futures, stock options; from 2026 also per index (NIFTY, BANKNIFTY ...) | `nsearchives.nseindia.com/content/fo/fii_stats_DD-Mon-YYYY.xls` (Excel 97 binary) | 200 for 01-Jan-2019, 02-Jan-2019, 05-Jul-2024, 15-Oct-2026, 21-Oct-2026 | 21 Oct's file `Last-Modified` 19:14 IST that day; old files' times are later rewrites (2 Jan 2019 file: 6 Mar 2019), so first publication is unknown for history | NSE archive file, the same kind as A1/A8's files; owner's personal-research rule (15 Oct) |
| **Participant-wise trading volume**: contracts bought and sold by Client, DII, FII, Pro in index and stock futures and options | `nsearchives.nseindia.com/content/nsccl/fao_participant_vol_DDMMYYYY.csv` | 200 for 02-Jan-2019 and 21-Oct-2026 | 21 Oct's file 19:14 IST; 2019's file rewritten 17 Jan 2019 | as above; A8 already archives the sister file (participant OI) |
| FII/DII **cash-market** values | NSE `api/fiidiiTradeReact` | latest day only; no NSE archive found | P8 captures daily from 13 Oct 2026 | — |
| NSDL **FPI** daily investment (equity, debt) | `www.fpi.nsdl.co.in/web/Reports/Archive.aspx` | an ASP.NET form by date (postback), no file links | the report date | NSDL's terms: "Reproduction, redistribution and transmission of any information contained on the website are strictly prohibited"; the page blocks save keys. **Not built** without the owner's explicit decision (open question 1) |

Layout note: the FII statistics file changed between 2019 (four rows: index futures, index options, stock futures,
stock options) and 2026 (the same four plus one row per index future and option). The reader keeps the four totals
for every year and the per-index rows where they exist.

## Scope

In:
1. Two dated `NseArchiveSource` datasets (`FiiDerivativeStatsSource`, `ParticipantVolumeSource`) with content checks,
   archived to Drive by A9's librarian (`python -m fno data-librarian <dataset>`), resumable, every file with its
   manifest row; history from 1 Jan 2019 (a back-fill of about 1,940 sessions each) and then daily (a small
   workflow at 21:30 IST plus a morning retry; failures alert once and go to O10 through capture-watch).
2. Readers: per session, FII buy, sell, net (crores and contracts) and OI for the four groups (and per index from its
   first day); participant volume per client type and group. A derived table `fii_flows.csv`-like part in Drive
   (O9 `PartTable`) with `available_from` = the next session after the trading date (conservative: recent files
   appear about 19:14 IST, and old files' publication times are lost).
3. A coverage check: every session from 2019 present, damaged or explained (A7 calendar; NSE's documented gaps).

Out: NSDL FPI history (terms; open question 1); NSE cash FII/DII history (no archive found); any forecaster use (a GR1
or later study decides); intraday flows.

## Acceptance criteria (good, bad, boundary and empty cases each)

1. Readers parse the real 2019 and 2026 layouts (fixtures of 02-Jan-2019 and 21-Oct-2026), giving the four group
   totals and net values; a damaged or HTML file is refused whole; an unknown extra row in a known section is kept
   as a per-index row only when its name ends in FUTURES or OPTIONS.
2. Point in time: `available_from` is the next session after the trading date (a Friday's file is available Monday;
   before a holiday, the session after it), never the same day.
3. Back-fill: the librarian fills 2019-01-01 to the latest session, resumable, with manifest rows; a 404 on a session
   is "not published" (alerted), a 404 on a holiday is not a gap.
4. Daily: the workflow runs after 19:14 IST with a retry, alerts on failure (fallback step pattern of judge 359), and
   is on O10's capture-watch list.
5. No value enters the repository (manifest rows and receipts only).
6. Real sample: the first back-filled month and the first daily run in the claims file.

## Gap list

| Requirement | Where |
|---|---|
| Past FII/DII (FPI) daily flows, 2019 on | criteria 1, 3 (FII derivatives and participant volume) |
| NSDL's FPI archive | Out until the owner decides (terms) |
| NSE's archives if they hold history | Step 0: FII stats and participant volume do; cash FII/DII does not |
| Read-only, write-once to Drive with receipts | criteria 3, 5 |
| Point-in-time dates (first published) | criterion 2 (conservative t+1; true first-publication times are lost for history, stated) |
| Verify the source and its terms before building | Step 0 |
| Goal: GR1 can test flows vs ranges | the derived table's columns; no forecaster wired (Out) |

## Open questions

1. **NSDL FPI equity history** (the closest to "FPI flows"): its terms prohibit reproduction and redistribution, and
   the archive is a form. Private, Drive-only storage is not redistribution, but automated form reads may breach the
   site's rules. The owner decides: skip (recommended until needed), or allow a slow one-time back-fill under the 15
   Oct personal-research rule.
2. `xlrd` (pure Python, free, pinned) to read the `.xls` files, as `pypdf` was approved for A20c.

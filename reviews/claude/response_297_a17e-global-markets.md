# Response 297: story A17e (global markets beyond the US), story text for judge F

Builder: A16b/A17 builder (session 01MBnbVU). Story text: `docs/stories/A17e-global-markets.md` on
`story/a17e-global-markets`. Lane 1. Asked by the orchestrator on 21 Oct 2026 for the owner's request of the same day.

## What is asked of the judge
Judge the story text before any code: the source table (Step 0), the split between what is built now (the three
sources whose terms allow it) and what waits for the owner (six decisions), and the acceptance criteria.

## Evidence behind Step 0
- Three research passes (Asia-Pacific closes, Europe and VIX, Asian levels before 09:15), 21 Oct 21:05-21:20 UTC.
  Each fetched the candidate URLs and read the terms pages. Their notes are summarised in the story's table, with
  every terms quote and URL.
- Re-run by me at 21:20 UTC: CSIndex returned 1,891 rows from 2019-01-01 to 2026-10-21; Nikkei's CSV runs from
  2023/01/04 to 2026/10/21, and its footer forbids copying without Nikkei's permission; TWSE's open-data API returned
  the current month only, newest 20 Oct.
- Not tested: FRED (maintenance page at both tries), SSE's own quote host (unreachable from here), and the Hang Seng
  and SGX terms pages, which render only by script.

## Boundary
Agreed with the A22 builder (013u1Ac2) on 21 Oct, and written into A22's story: A22's "Asia opens" row now reads
"A17e, not A22".

## Revision 1 (21 Oct, 21:40 UTC): the owner's new data rule (DESK_DECISIONS 50a79a43)
A source's redistribution terms no longer block a download for private research, so the story now picks the best
source, not the most permissive one. The three kept limits (Drive only, no getting around blocks, paced) are in the text.
- **Official publishers stay primary** where they answer without a login: CSIndex, TWSE OpenAPI, Nikkei's CSV, Cboe
  VIX and STOXX's 3-month files. KOSPI's official source waits for the owner's KRX key.
- **Yahoo's public chart API (no login) covers all eleven indexes back to 2019.** It is the history before each
  official file starts and the only source for Hang Seng, ASX 200, Straits Times and FTSE 100.
- **Yahoo checked against the official files (strong evidence):** Nikkei matches on 927 of 927 days. SSE matches on
  1,887 days, but Yahoo lacks 3 real sessions. VIX matches on 1,960 of 1,963 days, with one large error
  (2026-02-06: 20.37 against 17.76). So the reading prefers the official value, and every overlap is checked.
- **Part B added:** a pre-09:15 level for each Asian index from Yahoo's 5-minute chart. A22's routine calls it at
  08:50-09:05, and the first five sessions measure its delay.
- **The six owner decisions of the first text are gone.** Two optional improvements remain: the KRX key, and noting
  that Yahoo is not official.

## Revision 2 (21 Oct, 21:50 UTC): judge 431's findings, each checked before fixing
- **B1, accepted.** The story had no gap list, so I added one. It maps each market the owner named and each rule
  (A17's point-in-time rule, 50a79a43's three limits, O9, the A22 boundary, the alert rule, and quality rules 5, 6
  and 8) to a scope item, a criterion, or Out with its reason.
- **Minor 1, accepted.** Criterion 4 now tests `available_at` at, one minute before and one minute after each market's
  close in IST. That covers Australia's and Europe's 2026 clock changes, and an empty case where a missing date gives
  no label.
- **Minor 2, accepted with data.** The Asian closes are out by 10:40-14:30 IST, so the 14:11 cron could hold them. But
  GitHub started that cron 3 h 42 to 7 h 09 late on 17-21 Oct (measured), so it would miss the 15:45 report every day.
  Whether the report uses same-day Asian closes is FL1's decision. It is Out here, and the scope explains why.
- **Minor 3, partly accepted.** The goal is to drop the equality guess, and that is right. A calendar-based rule needs
  a Chinese exchange calendar we do not have; building it from Yahoo's dates would be circular. The rule I adopted
  instead: every CSIndex request starts ten days before the first wanted date, and every earlier row is dropped. The
  fake row can only be the request's first row, so it never enters a table, and a real flat close is never touched.
  Criterion 1 tests both a planted holiday start and a planted flat close.
- **Also fixed (my own find).** Refusing a whole Yahoo answer for one duplicate date would have lost ASX's whole
  back-fill. Now a duplicate date is left out and listed in the checks.

## Revision 3 (21 Oct, 22:00 UTC): judge 431 addendum 1 (judged at 3faedabb, before revision 2)
- **B1 was already fixed in revision 2 (febca555):** a gap list table. It now also names criterion 8.
- **SF1, accepted.** Kept rule 2 means a block must stop the cue and never be worked around. Scope 2 now says: on
  HTTP 401, 403 or 429, a consent or crumb page, or a CAPTCHA, the Yahoo cue stops for that run, writes nothing, and is
  named in the run's one alert line. It is never retried with a cookie, a crumb, another user agent or another
  address; the next scheduled run tries once more, the same plain way. New criterion 8 plants 401, 403, 429, a consent
  page and a CAPTCHA page, and checks exactly one request each, with the other cues still running.
- **Minor 1, accepted.** Hang Seng, ASX 200, Straits Times and FTSE 100 are labelled `unverified (Yahoo only)` in every
  reading and check line, because nothing official is there to compare against.
- **Minor 2, accepted.** Criterion 7 tests the stale rule at 20:00 (not stale) and 20:01 (stale).

## Code claims (story/a17e-global-markets; the head is in the message to judge F)

**What is built:**
- 7 official sources: CSIndex, TWSE, Nikkei, Cboe VIX, and STOXX for the DAX and the Euro Stoxx 50.
- 12 Yahoo cues, including the Nasdaq-100 of amendment 1. One Yahoo block stops every Yahoo cue of the run.
- `IndexReader`: one reading per index, the official value first.
- The official/Yahoo pair checks, with the dates kept in Drive and only the counts printed.
- The `behind` check at 09:15, alerted once per episode.
- Part B, `global-cues preopen`, with its statuses: live, stale, lunch break and market closed.
- Every value is private, kept in Drive. The repository gets snapshot log rows only.

**Real output** (quality rule 6). A dry run of `GlobalCueJob` over the world sources, 21 Oct 2026 21:50-22:00 UTC.
It made real downloads, with every file kept in a scratch folder: no Drive, no repository, and no level printed.
- Rows added:

  | Cue | Rows |
  |---|---|
  | `sse_composite` | 1,890 |
  | `taiex` | 14 |
  | `nikkei225` | 928 |
  | `vix_us` | 1,994 |
  | `eurostoxx50`, `dax` | 66 each |
  | Yahoo cues | 1,887 to 1,985 each, from 2019 |

  The run took 21 s.
- Comparisons:
  - DAX and Euro Stoxx 50: 65 dates, no difference.
  - Nikkei: 927 dates, no difference.
  - SSE: 1,887 dates; Yahoo lacks 2 real sessions (only_official 2).
  - VIX: 1,963 dates; 3 differ by more than 0.1%, including 6 Feb 2026.
  - Unverified (Yahoo only): asx200, ftse100, hang_seng, kospi, sti.
- Part B on the real Yahoo 5-minute answers at 03:00 IST: all 7 Asian indexes read `market closed`, which is correct
  because no Asian market was open yet.
- **Not proven yet (risk):** TWSE's open-data API reset the connection from this sandbox in 2 of 4 runs. When it
  does, `taiex: FAILED` and the run alerts, which is correct but noisy if it happens from GitHub's runners too. The
  first scheduled week will show it.

**Mutation proof** (quality rule 4). 24 mutations, one or more per criterion's code, each run against its test
file; all 24 were caught. Examples:
- the CSIndex window;
- the exchange-local date: the first try missed it, so I added the Sydney 23:00 UTC case;
- a tie going to the official value;
- the 0.1% tolerance;
- the Sydney and Shanghai closes;
- a world cue made public;
- the 20-minute stale rule;
- no O10 row;
- 429 not counted as a block;
- redirects followed;
- a consent page accepted;
- the shared gate off;
- a JSON error accepted;
- the range starting on the day itself;
- no lunch status;
- a setup failure not alerted;
- all-stale not alerted;
- the bar's start used instead of its end;
- holiday rows compared;
- behind never alerting;
- a short Nikkei row kept.

**Self-review by two independent agents** (quality rule 3). Both found the same blocking item:
- **Blocking, fixed:** a Drive failure while building part B's reader, or while writing its table, escaped without
  an alert or an O10 row. Now any failure alerts and records, and two new tests cover it.
- **Fixed:**
  - Tokyo's lunch break mislabelled as `stale` at 08:50.
  - Errors that could print a level (STOXX and TWSE dates and symbols, the CSIndex date, the part B level, a
    damaged pair cell).
  - A short Nikkei row or an impossible timestamp crashing the whole run (`IndexError` and `ArithmeticError` are now
    unreadable).
  - The certificate bundle: it now reads `CURL_CA_BUNDLE`, copes with a directory, and an `OSError` fails only its
    own cue.
  - Maximum ages shorter than real closures.
  - The shared host stop.
  - Yahoo's JSON error answer.
  - Sydney's first day missing from a range.
  - The bar's end time.
  - Strict pairing of times and closes.
  - Holiday rows on both sides.
  - All-stale alerting.
- **Kept, with the reason:**
  - TWSE's empty month start: amendment 2.6, measured on 2 Nov.
  - A duplicate date shows as a gap: amendment 3.5.
  - Part B's repository receipts (the `<index>_preopen.csv` snapshot logs, and O10's row) are committed by A22's
    routine line once it calls the command. That is the A22 builder's commit, agreed.

**Gates:** 9,031 passed and 17 xfailed (`-n auto`); ruff and the import check are clean.

**After the merge** (quality rule 8; owner f2293cea: live from the merge):
- the first scheduled `global-cues` run back-fills the world cues from 2019 into Drive, and its run is cited;
- A22 adds `python -m fno global-cues preopen` to its routine;
- I tell M1's owner about the Nasdaq-100 index reading.

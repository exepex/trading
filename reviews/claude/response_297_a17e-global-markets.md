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
